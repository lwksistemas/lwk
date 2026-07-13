"""Tarefas django-q para webhooks Asaas (worker lwks-worker)."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def run_asaas_global_webhook(payload: dict[str, Any]) -> None:
    from asaas_integration.sync_context import asaas_webhook_sync_only
    from asaas_integration.webhook_process import process_asaas_global_webhook_sync

    token = asaas_webhook_sync_only.set(True)
    try:
        process_asaas_global_webhook_sync(payload)
    except Exception:
        logger.exception("Webhook Asaas global: falha no worker")
        raise
    finally:
        asaas_webhook_sync_only.reset(token)


def run_asaas_loja_webhook(loja_id: int, payload: dict[str, Any]) -> None:
    from asaas_integration.sync_context import asaas_webhook_sync_only
    from crm_vendas.asaas_loja_webhook_process import process_asaas_loja_webhook_sync

    token = asaas_webhook_sync_only.set(True)
    try:
        process_asaas_loja_webhook_sync(loja_id, payload)
    except Exception:
        logger.exception("Webhook Asaas loja_id=%s: falha no worker", loja_id)
        raise
    finally:
        asaas_webhook_sync_only.reset(token)
