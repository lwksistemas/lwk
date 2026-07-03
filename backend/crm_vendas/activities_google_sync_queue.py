"""Fila assíncrona: sincronização de atividades com Google Calendar."""
from __future__ import annotations

import logging

from django.conf import settings
from django.db import close_old_connections

logger = logging.getLogger(__name__)


def _setup_tenant(loja_id: int) -> bool:
    from core.db_config import ensure_loja_database_config
    from superadmin.models import Loja
    from tenants.middleware import set_current_loja_id, set_current_tenant_db

    loja = Loja.objects.using('default').filter(id=loja_id).first()
    if not loja:
        return False
    db_name = getattr(loja, 'database_name', None) or f'loja_{getattr(loja, "slug", loja.id)}'.replace('-', '_')
    if not ensure_loja_database_config(db_name, conn_max_age=0) or db_name not in settings.DATABASES:
        return False
    set_current_loja_id(loja_id)
    set_current_tenant_db(db_name)
    return True


def enqueue_sync_atividade_create(loja_id: int, atividade_id: int, vendedor_id: int | None) -> None:
    from core.task_queue import enqueue_task

    enqueue_task(
        f'crm-gcal-create-{atividade_id}',
        'crm_vendas.activities_google_sync_queue.run_sync_atividade_create',
        loja_id,
        atividade_id,
        vendedor_id,
    )


def enqueue_sync_atividade_update(loja_id: int, atividade_id: int, vendedor_id: int | None) -> None:
    from core.task_queue import enqueue_task

    enqueue_task(
        f'crm-gcal-update-{atividade_id}',
        'crm_vendas.activities_google_sync_queue.run_sync_atividade_update',
        loja_id,
        atividade_id,
        vendedor_id,
    )


def enqueue_sync_atividade_delete(
    loja_id: int,
    google_event_id: str,
    vendedor_id: int | None = None,
) -> None:
    from core.task_queue import enqueue_task

    enqueue_task(
        f'crm-gcal-delete-{google_event_id[:32]}',
        'crm_vendas.activities_google_sync_queue.run_sync_atividade_delete',
        loja_id,
        google_event_id,
        vendedor_id,
    )


def dispatch_sync_atividade_create(request, atividade) -> None:
    if not atividade or not getattr(atividade, 'loja_id', None):
        return
    from .utils import get_current_vendedor_id

    enqueue_sync_atividade_create(
        atividade.loja_id,
        atividade.id,
        get_current_vendedor_id(request),
    )


def dispatch_sync_atividade_update(request, atividade) -> None:
    if not atividade or not getattr(atividade, 'loja_id', None):
        return
    from .utils import get_current_vendedor_id

    enqueue_sync_atividade_update(
        atividade.loja_id,
        atividade.id,
        get_current_vendedor_id(request),
    )


def dispatch_sync_atividade_delete(request, atividade, loja_id: int | None = None) -> None:
    if not atividade or not atividade.google_event_id:
        return
    from .utils import get_current_vendedor_id

    lid = loja_id or getattr(atividade, 'loja_id', None)
    if not lid:
        return
    enqueue_sync_atividade_delete(lid, atividade.google_event_id, get_current_vendedor_id(request))


def run_sync_atividade_create(loja_id: int, atividade_id: int, vendedor_id: int | None) -> None:
    from .activities_google_sync import sync_atividade_create_for_context
    from .models import Atividade

    close_old_connections()
    if not _setup_tenant(loja_id):
        logger.warning('Google sync create: tenant indisponível loja=%s', loja_id)
        return
    atividade = Atividade.objects.filter(id=atividade_id, loja_id=loja_id).first()
    if not atividade:
        logger.warning('Google sync create: atividade %s não encontrada', atividade_id)
        return
    sync_atividade_create_for_context(atividade, vendedor_id=vendedor_id)


def run_sync_atividade_update(loja_id: int, atividade_id: int, vendedor_id: int | None) -> None:
    from .activities_google_sync import sync_atividade_update_for_context
    from .models import Atividade

    close_old_connections()
    if not _setup_tenant(loja_id):
        logger.warning('Google sync update: tenant indisponível loja=%s', loja_id)
        return
    atividade = Atividade.objects.filter(id=atividade_id, loja_id=loja_id).first()
    if not atividade:
        logger.warning('Google sync update: atividade %s não encontrada', atividade_id)
        return
    sync_atividade_update_for_context(atividade, vendedor_id=vendedor_id)


def run_sync_atividade_delete(
    loja_id: int,
    google_event_id: str,
    vendedor_id: int | None = None,
) -> None:
    from .activities_google_sync import sync_atividade_delete_event

    close_old_connections()
    if not _setup_tenant(loja_id):
        logger.warning('Google sync delete: tenant indisponível loja=%s', loja_id)
        return
    sync_atividade_delete_event(loja_id, google_event_id, vendedor_id=vendedor_id)
