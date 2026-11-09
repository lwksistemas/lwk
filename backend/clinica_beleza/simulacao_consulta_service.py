"""Simulação da consulta. A quantidade não vai para a YouCam e não mexe no estoque."""
from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation

import requests
from django.utils import timezone

from core.encryption import decrypt_value
from core.media_storage import (
    assinar_url_midia,
    media_baixar_arquivo,
    media_delete_by_url,
    media_upload,
    parse_media_url,
    url_publica_midia,
)

logger = logging.getLogger(__name__)

from .models import PacienteFotoAcompanhamento, SimulacaoConsulta, SimulacaoEsteticaConfig
from .simulacao_estetica_service import SimulacaoEsteticaError
from .youcam_api import (
    YouCamClient,
    YouCamError,
    carimbar_aviso,
    endpoint_tarefa,
    interpretar_resposta,
    montar_pedido,
    preparar_imagem,
    resumo_pedido,
    unidades_da_resposta,
    unidades_tabela,
)


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


_NOTAS_VISIVEIS = {"pore", "texture", "wrinkle", "acne", "skin_age"}


def _leitura(item: dict) -> dict | None:
    tipo = str(item.get("type") or "")
    nota = item.get("ui_score")
    if tipo not in _NOTAS_VISIVEIS or not isinstance(nota, (int, float)):
        return None
    return {"tipo": tipo, "nota": nota}


def serializar(item: SimulacaoConsulta) -> dict:
    leituras = item.resultado_json if isinstance(item.resultado_json, list) else []
    foto_url = ""
    foto = getattr(item, "foto", None)
    if foto is not None and foto.url:
        foto_url = url_publica_midia(foto.url, ttl_seconds=2 * 60 * 60)
    return {
        "id": item.id,
        "modo": item.modo,
        "parametro": item.parametro,
        "intensidade": float(item.intensidade) if item.intensidade is not None else None,
        "quantidade": float(item.quantidade) if item.quantidade is not None else None,
        "status": item.status,
        "foto_url": foto_url,
        "resultado_url": url_publica_midia(item.resultado_url, ttl_seconds=2 * 60 * 60) if item.resultado_url else "",
        "leituras": [leitura for leitura in leituras if isinstance(leitura, dict) and leitura.get("nota") is not None],
        "erro": item.erro,
        "ilustrativa": True,
        "ciencia_visual": item.ciencia_visual,
        "created_at": timezone.localtime(item.created_at).isoformat() if item.created_at else "",
        "api_nome": item.api_nome or "Perfect Corp YouCam",
        "endpoint": item.endpoint,
        "pedido": item.pedido if isinstance(item.pedido, dict) else {},
        "profissional_nome": item.profissional_nome,
        "procedimento_nome": item.procedimento_nome,
        "unidades": item.unidades,
        "unidades_fonte": item.unidades_fonte,
        "imagem_na_clinica": bool(item.resultado_url and parse_media_url(item.resultado_url)),
    }


def listar(consulta_id: int) -> list[dict]:
    itens = SimulacaoConsulta.objects.filter(consulta_id=consulta_id).order_by("-created_at")[:30]
    return [serializar(item) for item in itens]


def _baixar_foto(url: str) -> bytes:
    if not parse_media_url(url):
        raise SimulacaoEsteticaError("A foto precisa estar no servidor de mídia da clínica.")
    conteudo = media_baixar_arquivo(url)
    if not conteudo:
        raise SimulacaoEsteticaError("Não foi possível ler a foto da consulta.")
    return preparar_imagem(conteudo)


def _endpoint(modo: str) -> str:
    try:
        return endpoint_tarefa(modo)
    except KeyError:
        return ""


def _nome_profissional(consulta) -> str:
    profissional = getattr(consulta, "professional", None)
    return getattr(profissional, "nome", "") or ""


def _nome_procedimento(consulta) -> str:
    agendamento = getattr(consulta, "appointment", None)
    if agendamento is not None:
        nomes = [
            nome
            for nome in agendamento.appointment_procedures.order_by("ordem", "id").values_list(
                "procedure__nome", flat=True,
            )
            if nome
        ]
        if nomes:
            return ", ".join(nomes)
    procedimento = getattr(consulta, "procedure", None)
    return getattr(procedimento, "nome", "") or ""


def _guardar_resultado(loja, url: str) -> str | None:
    try:
        resposta = requests.get(url, timeout=30)
    except requests.RequestException:
        return None
    if resposta.status_code != 200 or not resposta.content:
        return None
    try:
        conteudo = carimbar_aviso(resposta.content)
    except (OSError, ValueError):
        conteudo = resposta.content
    return media_upload(loja, conteudo, filename="simulacao.jpg", folder="fotos")


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
        api_nome="Perfect Corp YouCam",
        endpoint=_endpoint(modo),
        profissional_nome=_nome_profissional(consulta),
        procedimento_nome=_nome_procedimento(consulta),
    )
    registro.save()
    try:
        conteudo = _baixar_foto(foto.url)
        cliente = YouCamClient(chave)
        file_id = cliente.enviar_arquivo(conteudo)
        pedido = montar_pedido(
            modo,
            parametro,
            intensidade,
            file_id,
            assinar_url_midia(foto.url, ttl_seconds=30 * 60),
        )
        registro.pedido = resumo_pedido(pedido)
        registro.save(update_fields=["pedido", "updated_at"])
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
        salva = _guardar_resultado(loja, url)
        if not salva:
            cliente.apagar(registro.task_id)
            registro.task_id = ""
            registro.status = SimulacaoConsulta.STATUS_ERRO
            registro.erro = "O resultado chegou, mas não foi possível guardá-lo na clínica."
            registro.save(update_fields=["status", "erro", "task_id", "updated_at"])
            return serializar(registro)
        registro.resultado_url = salva
    registro.resultado_json = [
        leitura for item in saida if isinstance(item, dict) and (leitura := _leitura(item))
    ]
    debito = unidades_da_resposta(corpo)
    if debito is None:
        debito = unidades_tabela(registro.modo, registro.pedido if isinstance(registro.pedido, dict) else {})
        registro.unidades_fonte = "tabela" if debito is not None else ""
    else:
        registro.unidades_fonte = "resposta"
    registro.unidades = debito
    registro.status = SimulacaoConsulta.STATUS_PRONTA
    cliente.apagar(registro.task_id)
    registro.task_id = ""
    registro.save(update_fields=[
        "resultado_url", "resultado_json", "status", "task_id", "unidades", "unidades_fonte", "updated_at",
    ])
    return serializar(registro)


def excluir(loja, registro: SimulacaoConsulta) -> None:
    """Remove a geração. A foto original do paciente permanece."""
    if registro.task_id:
        try:
            YouCamClient(_chave(loja.id)).apagar(registro.task_id)
        except Exception:
            logger.warning("YouCam não apagou a tarefa da simulação %s", registro.id)
    if registro.resultado_url:
        media_delete_by_url(registro.resultado_url)
    registro.delete()


def marcar_ciencia(registro: SimulacaoConsulta) -> dict:
    if registro.status != SimulacaoConsulta.STATUS_PRONTA:
        raise SimulacaoEsteticaError("A ciência vale depois que o resultado estiver pronto.")
    registro.ciencia_visual = True
    registro.save(update_fields=["ciencia_visual", "updated_at"])
    return serializar(registro)
