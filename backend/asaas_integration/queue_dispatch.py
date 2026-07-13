"""Enfileira webhooks Asaas no lwks-backend (django-q + Redis)."""
from __future__ import annotations

from typing import Any


def should_enqueue_asaas_webhook() -> bool:
    from asaas_integration.sync_context import asaas_webhook_sync_only
    from core.task_queue import task_queue_enabled

    return task_queue_enabled() and not asaas_webhook_sync_only.get()


def _task_key(prefix: str, *parts: Any) -> str:
    label = "-".join(str(p) for p in parts if p not in (None, ""))
    return f'{prefix}-{label or "evt"}'


def enqueue_asaas_global_webhook(payload: dict[str, Any]) -> bool:
    from asaas_integration.webhook_process import GLOBAL_PAYMENT_EVENTS
    from core.task_queue import enqueue_task

    event = payload.get("event") or "unknown"
    payment = payload.get("payment") if isinstance(payload.get("payment"), dict) else {}
    payment_id = payment.get("id") or "no-payment"

    if event not in GLOBAL_PAYMENT_EVENTS or not payment:
        return False

    enqueue_task(
        _task_key("asaas-webhook", payment_id, event),
        "asaas_integration.queue_tasks.run_asaas_global_webhook",
        dict(payload),
    )
    return True


def enqueue_asaas_loja_webhook(loja_id: int, payload: dict[str, Any]) -> bool:
    from core.task_queue import enqueue_task

    event = payload.get("event") or payload.get("type") or "unknown"
    payment = payload.get("payment") if isinstance(payload.get("payment"), dict) else {}
    invoice = payload.get("invoice") if isinstance(payload.get("invoice"), dict) else {}
    ref = payment.get("id") or invoice.get("id") or abs(hash(str(payload))) % 10_000_000

    enqueue_task(
        _task_key("asaas-loja", loja_id, ref, event),
        "asaas_integration.queue_tasks.run_asaas_loja_webhook",
        loja_id,
        dict(payload),
    )
    return True
