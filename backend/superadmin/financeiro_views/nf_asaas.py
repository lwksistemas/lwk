"""Views de nota fiscal Asaas (superadmin)."""
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import FinanceiroLoja

logger = logging.getLogger(__name__)

def _get_asaas_client():
    """Retorna cliente Asaas configurado ou None."""
    from asaas_integration.client import AsaasClient
    from asaas_integration.models import AsaasConfig
    config = AsaasConfig.get_config()
    if not config or not config.api_key:
        return None
    return AsaasClient(api_key=config.api_key, sandbox=config.sandbox)


def _find_invoice_for_payment(client, payment_id):
    """Busca nota fiscal autorizada para um payment_id no Asaas."""
    response = client._make_request('GET', 'invoices', {'payment': payment_id})
    invoices = response.get('data', [])
    if not invoices:
        return None, invoices
    # Priorizar nota autorizada
    for inv in invoices:
        if inv.get('status') == 'AUTHORIZED':
            return inv, invoices
    return invoices[0], invoices
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nf_baixar_por_payment(request, payment_id):
    """Baixar PDF da nota fiscal de um pagamento específico do Asaas."""
    if not request.user.is_superuser:
        return Response({'detail': 'Apenas superadmin.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        client = _get_asaas_client()
        if not client:
            return Response({'success': False, 'error': 'Asaas não configurado'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        invoice, invoices = _find_invoice_for_payment(client, payment_id)
        if not invoice:
            return Response({'success': False, 'error': 'Nenhuma nota fiscal encontrada para este pagamento'}, status=status.HTTP_404_NOT_FOUND)

        status_nf = invoice.get('status')
        if status_nf != 'AUTHORIZED':
            return Response({'success': False, 'error': f'Nota fiscal não autorizada. Status: {status_nf}'}, status=status.HTTP_400_BAD_REQUEST)

        pdf_url = invoice.get('pdfUrl') or invoice.get('invoicePdfUrl') or invoice.get('invoiceUrl')
        if not pdf_url:
            return Response({'success': False, 'error': 'URL do PDF não disponível'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'success': True, 'pdf_url': pdf_url, 'invoice_id': invoice.get('id'), 'status': status_nf})
    except Exception as e:
        logger.exception("nf_baixar_por_payment: %s", e)
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nf_xml_por_payment(request, payment_id):
    """Retorna XML da nota fiscal (ISSNet direto ou Asaas)."""
    if not request.user.is_superuser:
        return Response({'detail': 'Apenas superadmin.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        # Primeiro tentar buscar XML local (emissão ISSNet direto)
        from superadmin.models import PagamentoLoja
        pagamento = PagamentoLoja.objects.filter(asaas_payment_id=payment_id).first()
        if pagamento and hasattr(pagamento, 'nfse_xml') and pagamento.nfse_xml:
            return Response({'success': True, 'xml': pagamento.nfse_xml})

        # Fallback: buscar via Asaas API
        client = _get_asaas_client()
        if not client:
            return Response({'success': False, 'error': 'Asaas não configurado e XML local não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        invoice, _ = _find_invoice_for_payment(client, payment_id)
        if not invoice:
            return Response({'success': False, 'error': 'Nenhuma nota fiscal encontrada'}, status=status.HTTP_404_NOT_FOUND)

        xml_url = invoice.get('xmlUrl') or invoice.get('invoiceXmlUrl')
        if xml_url:
            import requests as req
            resp = req.get(xml_url, timeout=15)
            if resp.status_code == 200:
                return Response({'success': True, 'xml': resp.text})

        return Response({'success': False, 'error': 'XML não disponível para esta nota'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.exception("nf_xml_por_payment: %s", e)
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def nf_reenviar_por_payment(request, payment_id):
    """Reenvia nota fiscal por email para o dono da loja do pagamento."""
    if not request.user.is_superuser:
        return Response({'detail': 'Apenas superadmin.'}, status=status.HTTP_403_FORBIDDEN)
    try:

        from asaas_integration.models import AsaasPayment as AP

        client = _get_asaas_client()
        if not client:
            return Response({'success': False, 'error': 'Asaas não configurado'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        invoice, _ = _find_invoice_for_payment(client, payment_id)
        if not invoice:
            return Response({'success': False, 'error': 'Nenhuma nota fiscal encontrada'}, status=status.HTTP_404_NOT_FOUND)

        if invoice.get('status') != 'AUTHORIZED':
            return Response({'success': False, 'error': f'NF não autorizada. Status: {invoice.get("status")}'}, status=status.HTTP_400_BAD_REQUEST)

        pdf_url = invoice.get('pdfUrl') or invoice.get('invoicePdfUrl') or invoice.get('invoiceUrl')
        if not pdf_url:
            return Response({'success': False, 'error': 'URL do PDF não disponível'}, status=status.HTTP_404_NOT_FOUND)

        # Buscar loja pelo pagamento
        payment_obj = AP.objects.filter(asaas_id=payment_id).select_related('customer').first()
        email_destino = None
        loja_nome = 'Loja'
        if payment_obj and payment_obj.customer:
            email_destino = payment_obj.customer.email
            loja_nome = payment_obj.customer.name
        if not email_destino:
            # Tentar via FinanceiroLoja
            fin = FinanceiroLoja.objects.filter(asaas_payment_id=payment_id).select_related('loja', 'loja__owner').first()
            if fin:
                email_destino = fin.loja.owner.email
                loja_nome = fin.loja.nome

        if not email_destino:
            return Response({'success': False, 'error': 'Email do destinatário não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        invoice_id = invoice.get('id')
        assunto = f'Nota Fiscal – Assinatura LWK Sistemas - {loja_nome}'
        corpo = (
            f'Olá,\n\n'
            f'Segue a nota fiscal referente à assinatura da loja {loja_nome}.\n\n'
            f'Nota Fiscal: {invoice_id}\n'
            f'Acesse a nota fiscal: {pdf_url}\n\n'
            f'Atenciosamente,\nEquipe LWK Sistemas'
        )
        from core.email_delivery import create_email_message, send_prepared
        msg = create_email_message(subject=assunto, body=corpo, to=[email_destino])
        send_prepared(msg, fail_silently=False)

        logger.info(f"✅ NF {invoice_id} reenviada para {email_destino}")
        return Response({'success': True, 'message': f'Nota fiscal reenviada para {email_destino}', 'invoice_id': invoice_id})
    except Exception as e:
        logger.exception("nf_reenviar_por_payment: %s", e)
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def nf_cancelar_por_payment(request, payment_id):
    """Cancela a nota fiscal de um pagamento específico no Asaas."""
    if not request.user.is_superuser:
        return Response({'detail': 'Apenas superadmin.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        client = _get_asaas_client()
        if not client:
            return Response({'success': False, 'error': 'Asaas não configurado'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        invoice, _ = _find_invoice_for_payment(client, payment_id)
        if not invoice:
            return Response({'success': False, 'error': 'Nenhuma nota fiscal encontrada'}, status=status.HTTP_404_NOT_FOUND)

        invoice_id = invoice.get('id')
        status_nf = invoice.get('status')

        if status_nf == 'CANCELED':
            return Response({'success': False, 'error': 'Nota fiscal já está cancelada'}, status=status.HTTP_400_BAD_REQUEST)

        client.cancel_invoice(invoice_id)
        logger.info(f"✅ NF {invoice_id} cancelada (payment: {payment_id})")
        return Response({'success': True, 'message': f'Nota fiscal {invoice_id} cancelada com sucesso', 'invoice_id': invoice_id})
    except Exception as e:
        logger.exception("nf_cancelar_por_payment: %s", e)
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
