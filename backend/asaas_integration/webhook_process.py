"""Processamento síncrono de webhooks Asaas (conta LWK global)."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

GLOBAL_PAYMENT_EVENTS = frozenset(
    {'PAYMENT_CREATED', 'PAYMENT_UPDATED', 'PAYMENT_CONFIRMED', 'PAYMENT_RECEIVED'}
)


def process_asaas_global_webhook_sync(payload: dict[str, Any]) -> dict[str, Any]:
    """Processa webhook da conta Asaas LWK (mensalidade das lojas)."""
    from asaas_integration.views_config._common import _asaas_webhook_log_context

    event_type = payload.get('event')
    payment_data = payload.get('payment', {})

    if not event_type or not payment_data:
        return {'success': True, 'status': 'ignored'}

    if event_type not in GLOBAL_PAYMENT_EVENTS:
        return {'success': True, 'status': 'ignored', 'reason': 'evento_nao_suportado'}

    logger.info('Webhook Asaas global (sync): %s', _asaas_webhook_log_context(payload))

    try:
        from superadmin.sync_service import AsaasSyncService

        resultado = AsaasSyncService().process_webhook_payment(payment_data)
    except ImportError:
        logger.error('Serviço de sincronização Asaas não disponível')
        return {'success': False, 'error': 'Serviço de sincronização não disponível'}

    if resultado.get('success'):
        logger.info('Webhook Asaas global processado: %s', resultado)
    else:
        logger.error('Erro ao processar webhook Asaas global: %s', resultado.get('error'))

    return resultado
