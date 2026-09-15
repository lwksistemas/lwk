"""Alinha o token do webhook LWK com o cadastro no painel Asaas."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

EVENTOS_PAGAMENTO = (
    "PAYMENT_CREATED",
    "PAYMENT_UPDATED",
    "PAYMENT_CONFIRMED",
    "PAYMENT_RECEIVED",
    "PAYMENT_OVERDUE",
    "PAYMENT_DELETED",
)


def _url_e_webhook_lwk(url: str) -> bool:
    return "/api/asaas/webhook" in (url or "")


def sincronizar_token_webhook_asaas(token: str | None = None) -> dict[str, Any]:
    """Grava o token do LWK no webhook da conta Asaas (authToken).

    Sem isso o Asaas envia o evento e o LWK responde 401 (token ausente/divergente).
    """
    from asaas_integration.client import AsaasClient
    from asaas_integration.models import AsaasConfig

    token = (token or AsaasConfig.resolve_webhook_token() or "").strip()
    if len(token) < 32:
        return {"success": False, "error": "token do webhook LWK ausente ou curto"}

    api_key = AsaasConfig.resolve_api_key()
    if not api_key:
        return {"success": False, "error": "chave API Asaas não configurada"}

    client = AsaasClient(api_key=api_key, sandbox=AsaasConfig.effective_sandbox(api_key))
    try:
        data = client._make_request("GET", "webhooks")
    except Exception as exc:
        logger.warning("Falha ao listar webhooks Asaas: %s", exc)
        return {"success": False, "error": str(exc)[:240]}

    items = data.get("data") if isinstance(data, dict) else []
    if not isinstance(items, list):
        items = []
    alvo = next((w for w in items if _url_e_webhook_lwk(w.get("url") or "")), None)
    if not alvo or not alvo.get("id"):
        return {"success": False, "error": "webhook LWK não encontrado no Asaas"}

    eventos = alvo.get("events") if isinstance(alvo.get("events"), list) else []
    if "PAYMENT_RECEIVED" not in eventos or "PAYMENT_CONFIRMED" not in eventos:
        eventos = list(dict.fromkeys([*eventos, *EVENTOS_PAGAMENTO]))

    payload = {
        "name": (alvo.get("name") or "LWK SISTEMAS").strip() or "LWK SISTEMAS",
        "url": alvo.get("url"),
        "email": alvo.get("email") or "",
        "enabled": True,
        "interrupted": False,
        "authToken": token,
        "sendType": alvo.get("sendType") or "SEQUENTIALLY",
        "events": eventos,
    }
    try:
        client._make_request("PUT", f"webhooks/{alvo['id']}", payload)
    except Exception as exc:
        logger.warning("Falha ao gravar token no webhook Asaas %s: %s", alvo.get("id"), exc)
        return {"success": False, "error": str(exc)[:240], "webhook_id": alvo.get("id")}

    logger.info("Token do webhook LWK gravado no Asaas (id=%s)", alvo.get("id"))
    return {"success": True, "webhook_id": alvo.get("id")}
