"""Enfileira webhooks Mercado Pago no lwks-backend (django-q + Redis)."""
from __future__ import annotations


def should_enqueue_mercadopago_webhook() -> bool:
    from core.task_queue import task_queue_enabled
    from superadmin.mercadopago_sync_context import mercadopago_webhook_sync_only

    return task_queue_enabled() and not mercadopago_webhook_sync_only.get()


def enqueue_mercadopago_webhook(payment_id: str) -> bool:
    from core.task_queue import enqueue_task

    pid = (payment_id or '').strip()
    if not pid:
        return False

    enqueue_task(
        f'mp-webhook-{pid}',
        'superadmin.mercadopago_queue_tasks.run_mercadopago_webhook',
        pid,
    )
    return True
