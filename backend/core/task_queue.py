"""
Fila de tarefas assíncronas (django-q + Redis).

Uso:
    from core.task_queue import enqueue_task
    enqueue_task('crm.retry_vendedor', 'crm_vendas.assinatura_vendedor_retry.run_retry_envio_vendedor', id, loja_id)

Com USE_TASK_QUEUE=false (dev sem worker), executa de forma síncrona.
"""
from __future__ import annotations

import logging
from importlib import import_module
from typing import Any, Callable

from django.conf import settings

logger = logging.getLogger(__name__)


def task_queue_enabled() -> bool:
    return bool(getattr(settings, 'USE_TASK_QUEUE', False))


def _resolve_callable(func_path: str) -> Callable[..., Any]:
    module_path, func_name = func_path.rsplit('.', 1)
    module = import_module(module_path)
    return getattr(module, func_name)


def enqueue_task(task_name: str, func_path: str, *args: Any, **kwargs: Any):
    """
    Enfileira tarefa no django-q ou executa inline se fila desabilitada.
    func_path: dotted path importável (ex.: 'whatsapp.tasks.send_lembretes_2h_whatsapp').
    """
    if not task_queue_enabled():
        logger.debug('Task queue off — executando sync: %s', task_name)
        func = _resolve_callable(func_path)
        return func(*args, **kwargs)

    from django_q.tasks import async_task

    return async_task(func_path, *args, task_name=task_name, **kwargs)


def queue_status() -> dict:
    """Status da fila para health check."""
    if not task_queue_enabled():
        return {'enabled': False, 'broker': 'disabled'}

    broker_name = 'redis' if getattr(settings, 'Q_CLUSTER', {}).get('redis') else 'orm'
    status = {'enabled': True, 'broker': broker_name}

    try:
        from django_q.broker import get_broker

        broker = get_broker()
        if hasattr(broker, 'queue_size'):
            status['queued'] = int(broker.queue_size())
    except Exception as exc:
        logger.debug('queue_status: não foi possível ler tamanho da fila: %s', exc)

    return status
