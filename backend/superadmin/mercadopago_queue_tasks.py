"""Tarefas django-q para webhooks Mercado Pago (worker lwks-worker)."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def run_mercadopago_webhook(payment_id: str) -> None:
    from superadmin.mercadopago_sync_context import mercadopago_webhook_sync_only
    from superadmin.sync_service import process_mercadopago_webhook_payment

    token = mercadopago_webhook_sync_only.set(True)
    try:
        result = process_mercadopago_webhook_payment(str(payment_id))
        if result.get("success"):
            logger.info("Webhook MP processado payment_id=%s: %s", payment_id, result)
        else:
            logger.error("Webhook MP falhou payment_id=%s: %s", payment_id, result.get("error"))
    except Exception:
        logger.exception("Webhook MP: falha no worker payment_id=%s", payment_id)
        raise
    finally:
        mercadopago_webhook_sync_only.reset(token)
