"""Fila assíncrona: geração de PDF + envio proposta/contrato ao cliente."""
from __future__ import annotations

import logging

from django.conf import settings
from django.db import close_old_connections

logger = logging.getLogger(__name__)


def _should_enqueue_documento_envio() -> bool:
    from core.task_queue import task_queue_enabled
    from crm_vendas.documento_sync_context import documento_envio_sync_only

    return task_queue_enabled() and not documento_envio_sync_only.get()


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


def enqueue_enviar_proposta_contrato_cliente(
    *,
    tipo: str,
    doc_id: int,
    loja_id: int,
    canal: str,
    user_id: int | None,
    public_api_base_url: str,
) -> None:
    from core.task_queue import enqueue_task

    enqueue_task(
        f'crm-doc-{tipo}-{doc_id}-{canal}',
        'crm_vendas.documento_envio_queue.run_enviar_proposta_contrato_cliente',
        tipo,
        doc_id,
        loja_id,
        canal,
        user_id,
        public_api_base_url,
    )


def run_enviar_proposta_contrato_cliente(
    tipo: str,
    doc_id: int,
    loja_id: int,
    canal: str,
    user_id: int | None,
    public_api_base_url: str,
) -> tuple[bool, str | None]:
    """Worker: gera PDF e envia (email/WhatsApp) sem re-enfileirar."""
    from core.email_sync_context import email_sync_only
    from crm_vendas.documento_sync_context import documento_envio_sync_only
    from crm_vendas.models import Contrato, Proposta
    from crm_vendas.views_enviar_cliente import _enviar_proposta_contrato_cliente_sync
    from whatsapp.sync_context import whatsapp_sync_only

    close_old_connections()
    doc_token = documento_envio_sync_only.set(True)
    email_token = email_sync_only.set(True)
    wa_token = whatsapp_sync_only.set(True)
    try:
        if not _setup_tenant(loja_id):
            return False, 'Loja indisponível para envio do documento.'

        if tipo == 'proposta':
            instance = (
                Proposta.objects.filter(id=doc_id, loja_id=loja_id)
                .select_related('oportunidade', 'oportunidade__lead')
                .prefetch_related('oportunidade__itens__produto_servico')
                .first()
            )
        elif tipo == 'contrato':
            instance = (
                Contrato.objects.filter(id=doc_id, loja_id=loja_id)
                .select_related('oportunidade', 'oportunidade__lead')
                .prefetch_related('oportunidade__itens__produto_servico')
                .first()
            )
        else:
            return False, 'Tipo de documento inválido.'

        if not instance:
            return False, 'Documento não encontrado.'

        user = None
        if user_id:
            from django.contrib.auth import get_user_model

            user = get_user_model().objects.filter(pk=user_id).first()

        ok, err = _enviar_proposta_contrato_cliente_sync(
            instance,
            canal,
            user=user,
            public_api_base_url=public_api_base_url,
        )
        if ok:
            logger.info(
                'Documento CRM enviado via fila: tipo=%s id=%s canal=%s loja=%s',
                tipo,
                doc_id,
                canal,
                loja_id,
            )
        else:
            logger.warning(
                'Falha envio documento via fila: tipo=%s id=%s canal=%s err=%s',
                tipo,
                doc_id,
                canal,
                err,
            )
        return ok, err
    except Exception as exc:
        logger.exception(
            'Erro worker envio documento CRM: tipo=%s id=%s loja=%s',
            tipo,
            doc_id,
            loja_id,
        )
        return False, str(exc)
    finally:
        whatsapp_sync_only.reset(wa_token)
        email_sync_only.reset(email_token)
        documento_envio_sync_only.reset(doc_token)
