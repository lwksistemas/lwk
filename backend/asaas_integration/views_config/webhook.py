"""Webhook e teste público Asaas."""
import logging

from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from ._common import AsaasClient, IsSuperAdmin, REQUESTS_AVAILABLE, _asaas_webhook_log_context

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([])  # Webhook público, sem autenticação
def asaas_webhook(request):
    """Webhook para receber notificações do Asaas (conta LWK — mensalidade)."""
    from asaas_integration.queue_dispatch import enqueue_asaas_global_webhook, should_enqueue_asaas_webhook
    from asaas_integration.webhook_process import GLOBAL_PAYMENT_EVENTS, process_asaas_global_webhook_sync
    from core.webhook_security import verify_asaas_access_token, webhook_auth_failed_response

    if not verify_asaas_access_token(request):
        return webhook_auth_failed_response()

    try:
        payload = request.data if isinstance(request.data, dict) else {}
        logger.info("Webhook Asaas recebido: %s", _asaas_webhook_log_context(payload))

        event_type = payload.get('event')
        payment_data = payload.get('payment', {})

        if not event_type or not payment_data:
            return Response({'status': 'ignored'}, status=status.HTTP_200_OK)

        if event_type not in GLOBAL_PAYMENT_EVENTS:
            return Response({'status': 'ignored'}, status=status.HTTP_200_OK)

        if should_enqueue_asaas_webhook():
            enqueue_asaas_global_webhook(payload)
            return Response({'status': 'received', 'queued': True}, status=status.HTTP_200_OK)

        resultado = process_asaas_global_webhook_sync(payload)

        if resultado.get('success'):
            response_data = {
                'status': resultado.get('status', 'processed'),
                'payment_id': resultado.get('payment_id'),
                'status_updated': resultado.get('status_updated', False),
            }
            if resultado.get('status') == 'ignored':
                response_data['reason'] = resultado.get('reason')
            if resultado.get('blocked'):
                response_data['loja_blocked'] = True
            if resultado.get('unblocked'):
                response_data['loja_unblocked'] = True
            return Response(response_data, status=status.HTTP_200_OK)

        logger.error('Erro ao processar webhook: %s', resultado.get('error'))
        return Response(
            {'status': 'error', 'error': resultado.get('error')},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as e:
        logger.error('Erro no webhook Asaas: %s', e)
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def asaas_test_public(request):
    """Testar conexão com a API do Asaas informando uma chave temporária."""

    if not REQUESTS_AVAILABLE or not AsaasClient:
        return Response(
            {'detail': 'Biblioteca requests não disponível. Instale com: pip install requests'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    try:
        api_key = request.data.get('api_key')
        if not api_key:
            return Response(
                {'detail': 'Chave da API é obrigatória no body da requisição'},
                status=status.HTTP_400_BAD_REQUEST
            )

        is_sandbox = 'hmlg' in api_key
        client = AsaasClient(api_key=api_key, sandbox=is_sandbox)

        result = client._make_request('GET', 'customers?limit=1')

        return Response({
            'message': 'Conexão testada com sucesso',
            'environment': 'Sandbox' if is_sandbox else 'Produção',
            'api_status': 'Conectado',
            'test_time': timezone.now().isoformat(),
            'customers_count': result.get('totalCount', 0),
            'api_key_masked': f"{api_key[:10]}...{api_key[-4:]}"
        })

    except Exception as e:
        logger.error(f"Erro ao testar API Asaas: {e}")
        return Response(
            {'detail': f'Erro na conexão: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
