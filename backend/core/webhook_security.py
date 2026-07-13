"""Validação de webhooks (Asaas, Mercado Pago).

Quando o token/secret está configurado, requisições inválidas são rejeitadas.
Em produção (WEBHOOK_STRICT_VERIFY=True), POST sem credencial configurada também é rejeitado.
"""
from __future__ import annotations

import hashlib
import hmac
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def webhook_strict_verify() -> bool:
    return bool(getattr(settings, "WEBHOOK_STRICT_VERIFY", not settings.DEBUG))


def _reject_unconfigured(provider: str) -> bool:
    """True = deve rejeitar (401)."""
    if webhook_strict_verify():
        logger.error("Webhook %s: token/secret não configurado (WEBHOOK_STRICT_VERIFY)", provider)
        return True
    logger.warning("Webhook %s: verificação desabilitada — configure o token em produção", provider)
    return False


def verify_asaas_access_token(request, expected_token: str | None = None) -> bool:
    """Valida header asaas-access-token (documentação Asaas).
    expected_token: override; senão usa token do banco, ASAAS_WEBHOOK_TOKEN ou ASAAS_LOJA_WEBHOOK_TOKEN.
    """
    token = (expected_token or "").strip()
    if not token:
        try:
            from asaas_integration.models import AsaasConfig
            token = AsaasConfig.resolve_webhook_token()
        except Exception:
            token = (getattr(settings, "ASAAS_WEBHOOK_TOKEN", None) or "").strip()
            if not token:
                token = (getattr(settings, "ASAAS_LOJA_WEBHOOK_TOKEN", None) or "").strip()

    if not token:
        return not _reject_unconfigured("Asaas")

    received = (request.headers.get("asaas-access-token") or "").strip()
    if not received or not hmac.compare_digest(received, token):
        logger.warning("Webhook Asaas: token inválido ou ausente")
        return False
    return True


def verify_mercadopago_signature(request, secret: str | None = None) -> bool:
    """Valida x-signature do Mercado Pago (HMAC SHA256 do manifest).
    """
    key = (secret or "").strip()
    if not key:
        key = (getattr(settings, "MERCADOPAGO_WEBHOOK_SECRET", None) or "").strip()

    if not key:
        return not _reject_unconfigured("Mercado Pago")

    x_signature = request.headers.get("x-signature") or ""
    x_request_id = request.headers.get("x-request-id") or ""
    if not x_signature:
        logger.warning("Webhook Mercado Pago: header x-signature ausente")
        return False

    data_id = request.GET.get("data.id") or request.GET.get("id") or ""
    if not data_id and isinstance(getattr(request, "data", None), dict):
        inner = request.data.get("data") or {}
        if isinstance(inner, dict):
            data_id = str(inner.get("id") or "")

    ts = v1 = None
    for part in x_signature.split(","):
        part = part.strip()
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        k, v = k.strip(), v.strip()
        if k == "ts":
            ts = v
        elif k == "v1":
            v1 = v

    if not ts or not v1:
        logger.warning("Webhook Mercado Pago: x-signature malformado")
        return False

    # data.id na query é obrigatório na validação oficial; sem ele não dá para validar com segurança
    if not data_id:
        logger.warning("Webhook Mercado Pago: data.id ausente na query — rejeitado")
        return False

    manifest = f"id:{data_id};request-id:{x_request_id};ts:{ts};"
    calculated = hmac.new(key.encode("utf-8"), manifest.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated, v1):
        logger.warning("Webhook Mercado Pago: assinatura inválida")
        return False
    return True


def webhook_auth_failed_response():
    from rest_framework import status
    from rest_framework.response import Response
    return Response({"detail": "Webhook não autorizado"}, status=status.HTTP_401_UNAUTHORIZED)
