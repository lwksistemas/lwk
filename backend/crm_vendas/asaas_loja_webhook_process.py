"""Processamento síncrono de webhooks Asaas por loja (conta CRM da empresa)."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def invoice_payload_para_sync(payload: dict) -> tuple[str, dict]:
    """
    Retorna (event, invoice_dict) para sincronizar NFSe.
    O Asaas envia `invoice` no corpo; em alguns eventos pode vir só em `payment`.
    """
    event = payload.get('event') or payload.get('type') or ''
    invoice = payload.get('invoice') if isinstance(payload.get('invoice'), dict) else {}
    if not invoice.get('id') and isinstance(payload.get('payment'), dict):
        pay = payload['payment']
        inv = pay.get('invoice') if isinstance(pay.get('invoice'), dict) else {}
        if inv.get('id'):
            invoice = inv
        elif pay.get('invoiceId'):
            invoice = {'id': pay.get('invoiceId'), 'status': pay.get('invoiceStatus')}
    return event, invoice


def process_asaas_loja_webhook_sync(loja_id: int, payload: dict[str, Any]) -> None:
    """Sincroniza NFS-e e comissões após webhook da conta Asaas da loja."""
    from django.conf import settings

    from core.db_config import ensure_loja_database_config
    from superadmin.models import Loja
    from tenants.middleware import set_current_loja_id, set_current_tenant_db

    loja = Loja.objects.using('default').filter(id=loja_id).first()
    if not loja:
        logger.warning('Webhook Asaas loja: loja_id=%s não encontrada', loja_id)
        return

    db_name = getattr(loja, 'database_name', None) or f'loja_{getattr(loja, "slug", loja.id)}'.replace('-', '_')
    if not ensure_loja_database_config(db_name, conn_max_age=0) or db_name not in settings.DATABASES:
        logger.warning('Webhook Asaas loja: schema %s indisponível', db_name)
        return

    set_current_loja_id(loja_id)
    set_current_tenant_db(db_name)

    event = payload.get('event') or payload.get('type')
    payment = payload.get('payment') if isinstance(payload.get('payment'), dict) else {}
    invoice = payload.get('invoice') if isinstance(payload.get('invoice'), dict) else {}

    logger.info(
        'Asaas webhook loja sync id=%s slug=%s event=%s payment_id=%s invoice_id=%s',
        loja.id,
        loja.slug,
        event,
        payment.get('id'),
        invoice.get('id'),
    )

    try:
        ev, inv = invoice_payload_para_sync(payload)
        if inv.get('id'):
            from nfse_integration.asaas_webhook_sync import sincronizar_nfse_com_webhook_invoice

            sincronizar_nfse_com_webhook_invoice(ev, inv)
    except Exception as sync_err:
        logger.warning('Falha ao sincronizar NFSe com webhook Asaas: %s', sync_err, exc_info=True)

    try:
        if event in ('PAYMENT_RECEIVED', 'PAYMENT_CONFIRMED') and payment.get('id'):
            from crm_vendas.models_relatorio_comissao import RelatorioComissao
            from crm_vendas.services_relatorio_comissao import processar_pagamento_comissao

            rc = RelatorioComissao.objects.filter(
                asaas_payment_id=payment['id'],
                status='aguardando_pagamento',
            ).first()
            if rc:
                logger.info('Pagamento confirmado para relatório comissão %s', rc.numero)
                processar_pagamento_comissao(rc)
    except Exception as rc_err:
        logger.warning('Falha ao processar pagamento de comissão: %s', rc_err, exc_info=True)
