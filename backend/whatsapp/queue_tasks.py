"""Tarefas django-q para envio WhatsApp (worker lwks-worker)."""
from __future__ import annotations

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def _setup_tenant(loja_id: int) -> bool:
    from core.db_config import ensure_loja_database_config
    from superadmin.models import Loja
    from tenants.middleware import set_current_loja_id, set_current_tenant_db

    loja = Loja.objects.using('default').filter(id=loja_id).first()
    if not loja:
        logger.warning('WhatsApp queue: loja_id=%s não encontrada', loja_id)
        return False

    db_name = getattr(loja, 'database_name', None) or f'loja_{getattr(loja, "slug", loja.id)}'.replace('-', '_')
    if not ensure_loja_database_config(db_name, conn_max_age=0) or db_name not in settings.DATABASES:
        logger.warning('WhatsApp queue: schema %s indisponível', db_name)
        return False

    set_current_loja_id(loja_id)
    set_current_tenant_db(db_name)
    return True


def _load_user(user_id):
    if not user_id:
        return None
    from django.contrib.auth import get_user_model

    return get_user_model().objects.using('default').filter(pk=user_id).first()


def run_send_whatsapp(telefone, mensagem, loja_id, user_id=None):
    from whatsapp.models import WhatsAppConfig
    from whatsapp.services import send_whatsapp
    from whatsapp.sync_context import whatsapp_sync_only

    token = whatsapp_sync_only.set(True)
    try:
        if not _setup_tenant(loja_id):
            return False, 'Loja indisponível para envio WhatsApp.'
        config = WhatsAppConfig.objects.filter(loja_id=loja_id).first()
        user = _load_user(user_id)
        return send_whatsapp(telefone=telefone, mensagem=mensagem, user=user, config=config)
    finally:
        whatsapp_sync_only.reset(token)


def run_send_whatsapp_document(telefone, document_url, filename, loja_id, user_id=None, caption=None):
    from whatsapp.models import WhatsAppConfig
    from whatsapp.services import send_whatsapp_document
    from whatsapp.sync_context import whatsapp_sync_only

    token = whatsapp_sync_only.set(True)
    try:
        if not _setup_tenant(loja_id):
            return False, 'Loja indisponível para envio WhatsApp.'
        config = WhatsAppConfig.objects.filter(loja_id=loja_id).first()
        user = _load_user(user_id)
        return send_whatsapp_document(
            telefone=telefone,
            document_url=document_url,
            filename=filename,
            caption=caption,
            user=user,
            config=config,
        )
    finally:
        whatsapp_sync_only.reset(token)
