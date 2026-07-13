"""Helpers compartilhados para serialização e validação de WhatsAppConfig."""
import logging

from rest_framework import status
from rest_framework.response import Response

from core.phone_utils import telefone_exibicao_brasileiro, telefone_internacional_br

from .connection_service import sync_evolution_connection
from .evolution_client import evolution_configured
from .models import WhatsAppConfig

logger = logging.getLogger(__name__)


def serialize_whatsapp_config(config, loja=None, *, sync_evolution=False):
    loja = loja or getattr(config, "_loja_cache", None) or getattr(config, "loja", None)
    owner_telefone = (getattr(loja, "owner_telefone", None) or "").strip() if loja else ""
    provider = getattr(config, "whatsapp_provider", WhatsAppConfig.PROVIDER_META) or WhatsAppConfig.PROVIDER_META
    if (
        sync_evolution
        and provider == WhatsAppConfig.PROVIDER_EVOLUTION
        and evolution_configured()
    ):
        try:
            sync_evolution_connection(config, fetch_qr=False)
        except Exception as exc:
            logger.warning(
                "Evolution sync ignorado loja_id=%s: %s",
                getattr(config, "loja_id", "?"),
                exc,
            )
    connection_status = getattr(config, "whatsapp_connection_status", WhatsAppConfig.CONNECTION_DISCONNECTED)
    connected_phone = (getattr(config, "whatsapp_connected_phone", None) or "").strip()
    evolution_ready = evolution_configured()

    payload = {
        "enviar_confirmacao": config.enviar_confirmacao,
        "enviar_lembrete_24h": config.enviar_lembrete_24h,
        "enviar_lembrete_2h": config.enviar_lembrete_2h,
        "enviar_cobranca": config.enviar_cobranca,
        "enviar_lembrete_tarefas": getattr(config, "enviar_lembrete_tarefas", True),
        "enviar_proposta_whatsapp": getattr(config, "enviar_proposta_whatsapp", True),
        "enviar_contrato_whatsapp": getattr(config, "enviar_contrato_whatsapp", True),
        "enviar_termo_consentimento_whatsapp": getattr(config, "enviar_termo_consentimento_whatsapp", True),
        "mensagem_confirmacao_agenda": (getattr(config, "mensagem_confirmacao_agenda", None) or "").strip(),
        "owner_telefone": telefone_exibicao_brasileiro(owner_telefone) if owner_telefone else "",
        "whatsapp_numero": telefone_exibicao_brasileiro((config.whatsapp_numero or "").strip()),
        "whatsapp_ativo": getattr(config, "whatsapp_ativo", False),
        "whatsapp_phone_id": (getattr(config, "whatsapp_phone_id", None) or "").strip(),
        "whatsapp_token_set": bool((getattr(config, "whatsapp_token", None) or "").strip()),
        "whatsapp_provider": provider,
        "whatsapp_connection_status": connection_status,
        "connection_status": connection_status,
        "whatsapp_connected_phone": connected_phone,
        "connected_phone": connected_phone,
        "whatsapp_connected_at": (
            config.whatsapp_connected_at.isoformat()
            if getattr(config, "whatsapp_connected_at", None) else None
        ),
        "evolution_available": evolution_ready,
    }
    return payload


def apply_whatsapp_config_patch(config, data):
    """Aplica PATCH parcial; retorna (update_fields, error_response)."""
    update_fields = ["updated_at"]

    bool_fields = (
        "enviar_confirmacao",
        "enviar_lembrete_24h",
        "enviar_lembrete_2h",
        "enviar_cobranca",
        "enviar_lembrete_tarefas",
        "enviar_proposta_whatsapp",
        "enviar_contrato_whatsapp",
        "enviar_termo_consentimento_whatsapp",
    )
    for key in bool_fields:
        if key in data:
            setattr(config, key, bool(data[key]))
            update_fields.append(key)

    if "whatsapp_numero" in data:
        raw = (data.get("whatsapp_numero") or "").strip()
        config.whatsapp_numero = telefone_internacional_br(raw)[:20] if raw else ""
        update_fields.append("whatsapp_numero")
    if "whatsapp_ativo" in data:
        config.whatsapp_ativo = bool(data["whatsapp_ativo"])
        update_fields.append("whatsapp_ativo")
    if "whatsapp_phone_id" in data:
        config.whatsapp_phone_id = (data.get("whatsapp_phone_id") or "").strip()[:64]
        update_fields.append("whatsapp_phone_id")
    if "whatsapp_token" in data:
        config.whatsapp_token = (data.get("whatsapp_token") or "").strip()[:512]
        update_fields.append("whatsapp_token")
    if "whatsapp_provider" in data:
        provider = (data.get("whatsapp_provider") or WhatsAppConfig.PROVIDER_META).strip().lower()
        if provider not in (WhatsAppConfig.PROVIDER_META, WhatsAppConfig.PROVIDER_EVOLUTION):
            return update_fields, Response({"error": "Provedor WhatsApp inválido."}, status=status.HTTP_400_BAD_REQUEST)
        config.whatsapp_provider = provider
        update_fields.append("whatsapp_provider")
    if "mensagem_confirmacao_agenda" in data:
        config.mensagem_confirmacao_agenda = (data.get("mensagem_confirmacao_agenda") or "").strip()
        update_fields.append("mensagem_confirmacao_agenda")

    err = validate_whatsapp_activation(config)
    if err:
        return update_fields, err
    return update_fields, None


def validate_whatsapp_activation(config):
    if not config.whatsapp_ativo:
        return None
    provider = getattr(config, "whatsapp_provider", WhatsAppConfig.PROVIDER_META) or WhatsAppConfig.PROVIDER_META
    if provider == WhatsAppConfig.PROVIDER_EVOLUTION:
        if not evolution_configured():
            return Response(
                {"error": "WhatsApp Web não está disponível no servidor (Evolution API não configurada)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if config.whatsapp_connection_status != WhatsAppConfig.CONNECTION_CONNECTED:
            sync_evolution_connection(config, fetch_qr=False)
        if config.whatsapp_connection_status != WhatsAppConfig.CONNECTION_CONNECTED:
            return Response(
                {
                    "error": (
                        "Conecte o WhatsApp Web escaneando o QR Code antes de ativar o envio."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return None

    phone_ok = bool((config.whatsapp_phone_id or "").strip())
    token_ok = bool((config.whatsapp_token or "").strip())
    if not phone_ok or not token_ok:
        return Response(
            {
                "error": (
                    "Cada loja usa seu próprio WhatsApp na Meta. "
                    "Informe Phone Number ID e token antes de ativar."
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    return None
