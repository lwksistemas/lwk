"""Tarefas django-q para emissão NFS-e (worker lwks-worker)."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def run_emitir_nfse_assinatura(pagamento_id: int, payment_id: str = '') -> None:
    from nfse_integration.sync_context import nfse_sync_only
    from superadmin.models import PagamentoLoja
    from superadmin.sync_service.nfse import emitir_nfse_assinatura_sync

    token = nfse_sync_only.set(True)
    try:
        pagamento = PagamentoLoja.objects.filter(id=pagamento_id).select_related('loja', 'loja__owner').first()
        if not pagamento:
            logger.warning('NFS-e fila: pagamento_id=%s não encontrado', pagamento_id)
            return
        emitir_nfse_assinatura_sync(pagamento, payment_id)
    finally:
        nfse_sync_only.reset(token)


def run_emissao_nfse_loja(loja_id: int, validated_data: dict) -> None:
    from django.db import close_old_connections

    from nfse_integration.loja_nfse_api import processar_emissao_nfse_loja_sync
    from nfse_integration.queue_serialize import deserialize_validated_data
    from nfse_integration.sync_context import nfse_sync_only
    from superadmin.models import Loja
    from tenants.middleware import _configure_tenant_db_for_loja, get_current_tenant_db

    close_old_connections()
    token = nfse_sync_only.set(True)
    try:
        loja = Loja.objects.using('default').filter(id=loja_id).first()
        if not loja:
            logger.warning('NFS-e fila loja: loja_id=%s não encontrada', loja_id)
            return
        if not _configure_tenant_db_for_loja(loja):
            logger.warning('NFS-e fila loja: tenant indisponível loja_id=%s', loja_id)
            return

        db_name = get_current_tenant_db()
        if db_name and db_name != 'default':
            try:
                from nfse_integration.schema_patch import patch_nfse_asaas_columns_if_missing

                patch_nfse_asaas_columns_if_missing(db_name)
            except Exception:
                logger.exception('NFS-e fila: falha patch schema %s', db_name)

        body, http_status = processar_emissao_nfse_loja_sync(
            loja, loja_id, deserialize_validated_data(validated_data)
        )
        if http_status >= 400:
            logger.warning(
                'NFS-e fila loja_id=%s falhou: %s',
                loja_id,
                body.get('error', body),
            )
    except Exception:
        logger.exception('NFS-e fila loja_id=%s: exceção na emissão', loja_id)
        raise
    finally:
        nfse_sync_only.reset(token)


def run_emitir_nfse_manual(payload_dict: dict) -> None:
    from asaas_integration.models_nfse_config import SuperadminNFSeConfig
    from nfse_integration.emissao_manual_superadmin import emitir_nfse_manual_superadmin
    from nfse_integration.queue_serialize import payload_emissao_manual_from_dict
    from nfse_integration.sync_context import nfse_sync_only

    token = nfse_sync_only.set(True)
    try:
        config = SuperadminNFSeConfig.get_config()
        payload = payload_emissao_manual_from_dict(payload_dict)
        emitir_nfse_manual_superadmin(config, payload)
    except Exception:
        logger.exception('NFS-e fila: falha emissão manual superadmin')
        raise
    finally:
        nfse_sync_only.reset(token)


def run_emitir_nfse_comissao(relatorio_id: int, loja_id: int) -> None:
    from crm_vendas.services_relatorio_comissao import emitir_nfse_comissao_sync
    from nfse_integration.sync_context import nfse_sync_only

    token = nfse_sync_only.set(True)
    try:
        emitir_nfse_comissao_sync(relatorio_id, loja_id)
    finally:
        nfse_sync_only.reset(token)
