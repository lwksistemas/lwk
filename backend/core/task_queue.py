"""
Fila de tarefas assíncronas (django-q + Redis).

Uso:
    from core.task_queue import enqueue_task
    enqueue_task('crm.retry_vendedor', 'crm_vendas.assinatura_vendedor_retry.run_retry_envio_vendedor', id, loja_id)

Com USE_TASK_QUEUE=false (dev sem worker), executa de forma síncrona.
"""
from __future__ import annotations

import logging
import os
from importlib import import_module
from typing import Any, Callable, Literal, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

QueueHealthLevel = Optional[Literal['degraded', 'unhealthy']]

QUEUE_BACKLOG_DEGRADED = int(os.environ.get('LWK_QUEUE_BACKLOG_DEGRADED', '50'))
QUEUE_BACKLOG_UNHEALTHY = int(os.environ.get('LWK_QUEUE_BACKLOG_UNHEALTHY', '200'))


def task_queue_enabled() -> bool:
    return bool(getattr(settings, 'USE_TASK_QUEUE', False))


def process_role() -> str:
    return (os.environ.get('LWK_PROCESS_ROLE') or 'web').strip() or 'web'


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
    """Status da fila para health check e monitoramento."""
    role = process_role()
    if not task_queue_enabled():
        return {'enabled': False, 'broker': 'disabled', 'role': role}

    cluster = getattr(settings, 'Q_CLUSTER', {})
    broker_name = 'redis' if cluster.get('redis') else 'orm'
    status: dict[str, Any] = {
        'enabled': True,
        'broker': broker_name,
        'role': role,
        'queued': 0,
        'workers_alive': 0,
        'clusters': 0,
    }

    try:
        from django_q.brokers import get_broker
        from django_q.status import Stat
        from django_q.tasks import queue_size as django_q_queue_size

        broker = get_broker()
        status['queued'] = int(django_q_queue_size(broker))

        stats = Stat.get_all(broker) or []
        status['clusters'] = len(stats)
        status['workers_alive'] = sum(len(getattr(stat, 'workers', []) or []) for stat in stats)
        if role == 'web' and status['workers_alive'] == 0:
            status['worker_warning'] = True

        try:
            from datetime import timedelta

            from django.utils import timezone
            from django_q.models import Failure

            since = timezone.now() - timedelta(hours=24)
            status['failures_24h'] = Failure.objects.filter(stopped__gte=since).count()
        except Exception as exc:
            logger.debug('queue_status: failures_24h indisponível: %s', exc)
    except Exception as exc:
        logger.warning('queue_status: falha ao consultar fila: %s', exc)
        status['error'] = str(exc)[:120]

    return status


def queue_health_level(status: dict | None = None) -> QueueHealthLevel:
    """
    Avalia saúde operacional da fila.
    Retorna None quando OK; 'degraded' ou 'unhealthy' quando há risco.
    """
    status = status or queue_status()
    if not status.get('enabled'):
        return None

    queued = int(status.get('queued') or 0)
    if queued >= QUEUE_BACKLOG_UNHEALTHY:
        return 'unhealthy'
    if queued >= QUEUE_BACKLOG_DEGRADED:
        return 'degraded'

    role = status.get('role') or process_role()
    workers = status.get('workers_alive')
    if role == 'web' and workers == 0 and not status.get('error'):
        queued = int(status.get('queued') or 0)
        if queued > 0:
            return 'degraded'

    return None
