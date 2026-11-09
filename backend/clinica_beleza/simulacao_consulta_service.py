"""Simulação da consulta. A quantidade não vai para a YouCam e não mexe no estoque."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

import requests
from django.utils import timezone

from core.encryption import decrypt_value
from core.media_storage import media_upload_from_url, parse_media_url

from .models import PacienteFotoAcompanhamento, SimulacaoConsulta, SimulacaoEsteticaConfig
from .simulacao_estetica_service import SimulacaoEsteticaError
from .youcam_api import YouCamClient, YouCamError, interpretar_resposta, montar_pedido, preparar_imagem


def _chave(loja_id: int) -> str:
    from superadmin.plano_features import loja_plano_permite_simulacao_estetica

    disponivel, mensagem = loja_plano_permite_simulacao_estetica(loja_id)
    if not disponivel:
        raise SimulacaoEsteticaError(mensagem or "Plano sem simulação estética.", status=403)
    config = SimulacaoEsteticaConfig.objects.first()
    chave = decrypt_value(config.api_key) if config else ""
    if not config or not config.ativa or not chave:
        raise SimulacaoEsteticaError(
            "Ative a chave YouCam desta clínica em Configurações antes de simular.",
        )
    return chave


def _quantidade(valor) -> Decimal | None:
    if valor in (None, ""):
        return None
    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, ValueError) as exc:
        raise SimulacaoEsteticaError("Informe a quantidade planejada como número.") from exc
    if numero < 0:
        raise SimulacaoEsteticaError("A quantidade planejada não pode ser negativa.")
    return numero


def _leitura(item: dict) -> dict:
    nota = item.get("ui_score")
    return {"tipo": str(item.get("type") or ""), "nota": nota if isinstance(nota, (int, float)) else None}


def serializar(item: SimulacaoConsulta) -> dict:
    leituras = item.resultado_json if isinstance(item.resultado_json, list) else []
    return {
        "id": item.id,
        "modo": item.modo,
        "parametro": item.parametro,
        "intensidade": float(item.intensidade) if item.intensidade is not None else None,
        "quantidade": float(item.quantidade) if item.quantidade is not None else None,
        "status": item.status,
        "resultado_url": item.resultado_url,
        "leituras": leituras,
        "erro": item.erro,
        "ilustrativa": True,
        "ciencia_visual": item.ciencia_visual,
        "created_at": timezone.localtime(item.created_at).isoformat() if item.created_at else "",
    }


def listar(consulta_id: int) -> list[dict]:
    itens = SimulacaoConsulta.objects.filter(consulta_id=consulta_id).order_by("-created_at")[:30]
    return [serializar(item) for item in itens]


def _baixar_foto(url: str) -> bytes:
    if not parse_media_url(url):
        raise SimulacaoEsteticaError("A foto precisa estar no servidor de mídia da clínica.")
    try:
        resposta = requests.get(url, timeout=20)
    except requests.RequestException as exc:
        raise SimulacaoEsteticaError("Não foi possível ler a foto da consulta.") from exc
    if resposta.status_code != 200 or not resposta.content:
        raise SimulacaoEsteticaError("Não foi possível ler a foto da consulta.")
    return preparar_imagem(resposta.content)


def iniciar(loja, consulta, dados: dict) -> dict:
    loja_id = getattr(loja, "id", None) or getattr(consulta, "loja_id", None)
    chave = _chave(loja_id)
    if consulta.status not in ("IN_PROGRESS", "RECEBER"):
        raise SimulacaoEsteticaError("A simulação fica disponível com a consulta em andamento.")
    foto = PacienteFotoAcompanhamento.objects.filter(
        pk=dados.get("foto_id"),
        patient_id=consulta.patient_id,
    ).first()
    if foto is None:
        raise SimulacaoEsteticaError("Escolha uma foto deste paciente.")
    modo = str(dados.get("modo") or "")
    parametro = str(dados.get("parametro") or "")
    try:
        intensidade = float(dados.get("intensidade") or 0)
    except (TypeError, ValueError) as exc:
        raise SimulacaoEsteticaError("Informe a intensidade visual como número.") from exc
    registro = SimulacaoConsulta(
        consulta=consulta,
        foto=foto,
        modo=modo,
        parametro=parametro,
        intensidade=Decimal(str(intensidade)) if modo != "analise" else None,
        quantidade=_quantidade(dados.get("quantidade")),
        status=SimulacaoConsulta.STATUS_PROCESSANDO,
    )
    registro.save()
    try:
        conteudo = _baixar_foto(foto.url)
        cliente = YouCamClient(chave)
        file_id = cliente.enviar_arquivo(conteudo)
        pedido = montar_pedido(modo, parametro, intensidade, file_id, foto.url)
        registro.task_id = cliente.criar_tarefa(modo, pedido)
        registro.save(update_fields=["task_id", "updated_at"])
    except (YouCamError, SimulacaoEsteticaError) as exc:
        registro.status = SimulacaoConsulta.STATUS_ERRO
        registro.erro = exc.message
        registro.save(update_fields=["status", "erro", "updated_at"])
    except (requests.RequestException, OSError):
        registro.status = SimulacaoConsulta.STATUS_ERRO
        registro.erro = "Não foi possível enviar a foto para a YouCam."
        registro.save(update_fields=["status", "erro", "updated_at"])
    return serializar(registro)


def acompanhar(loja, registro: SimulacaoConsulta) -> dict:
    if registro.status != SimulacaoConsulta.STATUS_PROCESSANDO or not registro.task_id:
        return serializar(registro)
    try:
        chave = _chave(registro.loja_id)
    except SimulacaoEsteticaError as exc:
        registro.status = SimulacaoConsulta.STATUS_ERRO
        registro.erro = exc.message
        registro.save(update_fields=["status", "erro", "updated_at"])
        return serializar(registro)
    try:
        cliente = YouCamClient(chave)
        corpo = cliente.consultar(registro.modo, registro.task_id)
    except requests.RequestException:
        return serializar(registro)
    except YouCamError as exc:
        registro.status = SimulacaoConsulta.STATUS_ERRO
        registro.erro = exc.message
        registro.save(update_fields=["status", "erro", "updated_at"])
        return serializar(registro)
    estado, url, saida = interpretar_resposta(corpo)
    if estado == "processando":
        return serializar(registro)
    if estado == "erro":
        from .youcam_api import mensagem_erro

        registro.status = SimulacaoConsulta.STATUS_ERRO
        registro.erro = mensagem_erro(corpo)
        cliente.apagar(registro.task_id)
        registro.task_id = ""
        registro.save(update_fields=["status", "erro", "task_id", "updated_at"])
        return serializar(registro)
    if url:
        salva = media_upload_from_url(loja, url, folder="fotos")
        if not salva:
            cliente.apagar(registro.task_id)
            registro.task_id = ""
            registro.status = SimulacaoConsulta.STATUS_ERRO
            registro.erro = "O resultado chegou, mas não foi possível guardá-lo na clínica."
            registro.save(update_fields=["status", "erro", "task_id", "updated_at"])
            return serializar(registro)
        registro.resultado_url = salva
    registro.resultado_json = [_leitura(item) for item in saida if isinstance(item, dict)]
    registro.status = SimulacaoConsulta.STATUS_PRONTA
    cliente.apagar(registro.task_id)
    registro.task_id = ""
    registro.save(update_fields=["resultado_url", "resultado_json", "status", "task_id", "updated_at"])
    return serializar(registro)


def marcar_ciencia(registro: SimulacaoConsulta) -> dict:
    if registro.status != SimulacaoConsulta.STATUS_PRONTA:
        raise SimulacaoEsteticaError("A ciência vale depois que o resultado estiver pronto.")
    registro.ciencia_visual = True
    registro.save(update_fields=["ciencia_visual", "updated_at"])
    return serializar(registro)
