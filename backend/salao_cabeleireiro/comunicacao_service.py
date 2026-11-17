"""Envio do salão. Cada aviso só sai se o administrador ligou aquela regra."""
import logging
from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone

from .mensagens import (
    na_janela_lembrete,
    texto_cancelamento,
    texto_confirmacao,
    texto_lembrete,
    texto_reagendamento,
)
from .models import Agendamento, SalaoConfig

logger = logging.getLogger(__name__)

EVENTOS = ("confirmacao", "lembrete", "reagendamento", "cancelamento")
_CAMPO = {
    "confirmacao": "enviar_confirmacao",
    "lembrete": "enviar_lembrete",
    "reagendamento": "enviar_reagendamento",
    "cancelamento": "enviar_cancelamento",
}


def regras_de(config: SalaoConfig | None) -> dict:
    horas = int(getattr(config, "lembrete_horas", 24) or 24)
    if horas not in (2, 24):
        horas = 24
    return {
        "confirmacao": bool(getattr(config, "enviar_confirmacao", False)),
        "lembrete": bool(getattr(config, "enviar_lembrete", False)),
        "lembrete_horas": horas,
        "reagendamento": bool(getattr(config, "enviar_reagendamento", False)),
        "cancelamento": bool(getattr(config, "enviar_cancelamento", False)),
    }


def whatsapp_pronto(loja_id) -> bool:
    from whatsapp.models import WhatsAppConfig

    config = WhatsAppConfig.objects.filter(loja_id=loja_id).first()
    if config is None or not config.whatsapp_ativo:
        return False
    if config.whatsapp_provider == WhatsAppConfig.PROVIDER_EVOLUTION:
        return config.whatsapp_connection_status == WhatsAppConfig.CONNECTION_CONNECTED
    return bool((config.whatsapp_phone_id or "").strip() and (config.whatsapp_token or "").strip())


def _texto(agendamento, evento, salao):
    inicio = timezone.localtime(agendamento.inicio)
    nome = agendamento.cliente.nome
    from .procedimentos_service import nomes_do_agendamento

    servico = nomes_do_agendamento(agendamento)
    profissional = agendamento.profissional.nome
    if evento == "confirmacao":
        return texto_confirmacao(nome=nome, servico=servico, profissional=profissional, inicio=inicio, salao=salao)
    if evento == "lembrete":
        return texto_lembrete(nome=nome, servico=servico, profissional=profissional, inicio=inicio, salao=salao)
    if evento == "reagendamento":
        return texto_reagendamento(nome=nome, servico=servico, profissional=profissional, inicio=inicio, salao=salao)
    return texto_cancelamento(nome=nome, servico=servico, inicio=inicio, salao=salao)


def _reservar(loja_id, evento, agendamento_id, marca) -> bool:
    chave = f"salao-wa:{loja_id}:{evento}:{agendamento_id}:{marca}"
    return cache.add(chave, 1, timeout=60 * 60 * 36)


def _liberar(loja_id, evento, agendamento_id, marca):
    cache.delete(f"salao-wa:{loja_id}:{evento}:{agendamento_id}:{marca}")


def enviar_evento(agendamento, evento, *, user=None, salao_nome="", manual=False) -> tuple[bool, str]:
    if evento not in EVENTOS:
        return False, "Escolha confirmação, lembrete, reagendamento ou cancelamento."
    config = SalaoConfig.objects.first()
    ligado = bool(getattr(config, _CAMPO[evento], False))
    if not ligado:
        if manual:
            return False, "Ative esta mensagem nas configurações do salão."
        return False, ""
    from tenants.middleware import get_current_loja_id
    from whatsapp.models import WhatsAppConfig
    from whatsapp.services import send_whatsapp

    loja_id = get_current_loja_id()
    if not whatsapp_pronto(loja_id):
        return False, "O WhatsApp desta loja não está conectado."
    telefone = (agendamento.cliente.telefone or "").strip()
    if not telefone:
        return False, "O cliente está sem telefone."
    if not salao_nome and loja_id:
        from superadmin.models import Loja
        loja = Loja.objects.filter(pk=loja_id).only("nome").first()
        salao_nome = loja.nome if loja else "o salão"
    marca = timezone.localtime(agendamento.inicio).strftime("%Y%m%d%H%M")
    if not manual and not _reservar(loja_id, evento, agendamento.id, marca):
        return True, ""
    try:
        ok, erro = send_whatsapp(
            telefone,
            _texto(agendamento, evento, salao_nome or "o salão"),
            user=user,
            config=WhatsAppConfig.objects.filter(loja_id=loja_id).first(),
        )
    except Exception:
        logger.exception("WhatsApp do salão falhou no agendamento %s", agendamento.id)
        if not manual:
            _liberar(loja_id, evento, agendamento.id, marca)
        return False, "Não foi possível enviar o WhatsApp."
    if not ok and not manual:
        _liberar(loja_id, evento, agendamento.id, marca)
    return ok, erro or ""


def avisar_mudanca(agendamento, *, inicio_anterior, status_anterior, user=None) -> str:
    try:
        if agendamento.status == "CANCELLED" and status_anterior != "CANCELLED":
            _ok, erro = enviar_evento(agendamento, "cancelamento", user=user)
            return erro
        if agendamento.inicio != inicio_anterior and agendamento.status in ("SCHEDULED", "CONFIRMED", "IN_PROGRESS"):
            _ok, erro = enviar_evento(agendamento, "reagendamento", user=user)
            return erro
    except Exception:
        logger.exception("Aviso de WhatsApp do salão não bloqueou a agenda %s", agendamento.id)
        return ""
    return ""


def lembretes_da_loja(salao_nome: str) -> int:
    config = SalaoConfig.objects.first()
    regras = regras_de(config)
    if not regras["lembrete"]:
        return 0
    agora = timezone.localtime()
    horas = regras["lembrete_horas"]
    margem = timedelta(hours=3 if horas == 2 else 26)
    candidatos = Agendamento.objects.filter(
        inicio__gte=agora,
        inicio__lte=agora + margem,
        status__in=("SCHEDULED", "CONFIRMED"),
    ).select_related("cliente", "profissional", "servico")
    enviados = 0
    for agendamento in candidatos:
        if not na_janela_lembrete(timezone.localtime(agendamento.inicio), agora, horas):
            continue
        ok, _erro = enviar_evento(agendamento, "lembrete", salao_nome=salao_nome)
        if ok:
            enviados += 1
    return enviados


def validar_regras(dados) -> dict:
    horas = int(dados.get("lembrete_horas") or 24)
    if horas not in (2, 24):
        raise ValueError("O lembrete pode sair 2 horas ou 24 horas antes.")
    return {
        "enviar_confirmacao": bool(dados.get("confirmacao")),
        "enviar_lembrete": bool(dados.get("lembrete")),
        "lembrete_horas": horas,
        "enviar_reagendamento": bool(dados.get("reagendamento")),
        "enviar_cancelamento": bool(dados.get("cancelamento")),
    }

