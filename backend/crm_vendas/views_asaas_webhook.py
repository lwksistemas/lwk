"""
Webhook Asaas por loja — conta Asaas da própria empresa (NFS-e / cobranças no CRM).

Cada loja configura no painel Asaas (Integrações → Webhooks) a URL:
  POST {API}/api/crm-vendas/webhooks/asaas/<slug_loja>/

O slug é o mesmo da URL do app (/loja/<slug>/…), em geral o CNPJ só com dígitos.
Não usar o endpoint global /api/asaas/webhook/ — esse é da conta LWK (mensalidade).
"""
import logging

from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from crm_vendas.asaas_loja_webhook_process import process_asaas_loja_webhook_sync
from tenants.middleware import resolve_loja_from_slug_or_cnpj, _configure_tenant_db_for_loja

logger = logging.getLogger(__name__)


@csrf_exempt
@api_view(['GET', 'POST', 'HEAD'])
@permission_classes([AllowAny])
def asaas_loja_webhook(request, loja_slug: str):
    """
    Recebe notificações do Asaas da conta configurada na loja (API Key em CRM).

    GET/HEAD: confirma que a URL está correta (teste no painel ou navegador).
    POST: eventos PAYMENT_*, INVOICE_* etc. — valida token e enfileira ou processa sync.
    """
    loja = resolve_loja_from_slug_or_cnpj(loja_slug.strip())
    if not loja:
        return Response(
            {'error': 'Loja não encontrada para este slug', 'slug': loja_slug},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method in ('GET', 'HEAD'):
        return Response(
            {
                'ok': True,
                'message': 'Webhook Asaas da loja ativo. Use esta URL no painel Asaas (POST).',
                'loja_slug': loja.slug,
                'loja_id': loja.id,
                'metodo': request.method,
            },
            status=status.HTTP_200_OK,
        )

    if not _configure_tenant_db_for_loja(loja, request):
        logger.warning('asaas_loja_webhook: falha ao configurar tenant loja_id=%s', loja.id)

    from asaas_integration.queue_dispatch import enqueue_asaas_loja_webhook, should_enqueue_asaas_webhook
    from core.webhook_security import verify_asaas_access_token, webhook_auth_failed_response
    from crm_vendas.models_config import CRMConfig

    loja_token = CRMConfig.resolve_asaas_webhook_token(loja.id)
    if not verify_asaas_access_token(request, expected_token=loja_token or None):
        return webhook_auth_failed_response()

    payload = request.data if isinstance(request.data, dict) else {}
    event = payload.get('event') or payload.get('type')
    payment = payload.get('payment') if isinstance(payload.get('payment'), dict) else {}
    invoice = payload.get('invoice') if isinstance(payload.get('invoice'), dict) else {}

    logger.info(
        'Asaas webhook loja slug=%s id=%s event=%s payment_id=%s invoice_id=%s',
        loja.slug,
        loja.id,
        event,
        payment.get('id'),
        invoice.get('id'),
    )

    if should_enqueue_asaas_webhook():
        enqueue_asaas_loja_webhook(loja.id, payload)
        return Response(
            {
                'status': 'received',
                'queued': True,
                'loja_slug': loja.slug,
                'event': event,
            },
            status=status.HTTP_200_OK,
        )

    process_asaas_loja_webhook_sync(loja.id, payload)

    return Response(
        {
            'status': 'received',
            'loja_slug': loja.slug,
            'event': event,
        },
        status=status.HTTP_200_OK,
    )
