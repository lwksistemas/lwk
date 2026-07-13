"""
ViewSet para pagamentos Asaas
"""
import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AsaasConfig, AsaasPayment
from .serializers import AsaasPaymentSerializer
from .views_config import REQUESTS_AVAILABLE, IsSuperAdmin

# Importação condicional do cliente Asaas
if REQUESTS_AVAILABLE:
    try:
        from .client import AsaasClient
    except ImportError:
        AsaasClient = None
else:
    AsaasClient = None

logger = logging.getLogger(__name__)


class AsaasPaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para pagamentos Asaas (somente leitura para superadmin)"""
    serializer_class = AsaasPaymentSerializer
    permission_classes = [IsSuperAdmin]
    queryset = AsaasPayment.objects.all().select_related('customer')
    
    def get_queryset(self):
        """Filtrar pagamentos com ordenação"""
        queryset = super().get_queryset()
        
        # Filtros opcionais
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-due_date')
    
    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """Baixar PDF do boleto"""
        try:
            payment = self.get_object()
            
            if not payment.asaas_id:
                return Response(
                    {'error': 'Pagamento não possui ID do Asaas'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not AsaasClient:
                return Response(
                    {'error': 'Serviço Asaas não disponível'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Obter configuração
            config = AsaasConfig.get_config()
            if not config or not config.api_key:
                return Response(
                    {'error': 'Asaas não configurado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar se o pagamento é do tipo boleto
            if payment.billing_type != 'BOLETO':
                return Response(
                    {'error': 'PDF disponível apenas para pagamentos do tipo boleto'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Baixar PDF
            client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
            
            try:
                pdf_content = client.get_payment_pdf(payment.asaas_id)
                
                if pdf_content and len(pdf_content) > 0:
                    from django.http import HttpResponse
                    response = HttpResponse(pdf_content, content_type='application/pdf')
                    response['Content-Disposition'] = f'inline; filename="boleto_{payment.asaas_id}.pdf"'
                    response['Content-Length'] = len(pdf_content)
                    response['Cache-Control'] = 'no-cache'
                    return response
                else:
                    return Response(
                        {'error': 'PDF vazio ou não disponível'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            except Exception as pdf_error:
                logger.error(f"Erro específico ao baixar PDF: {pdf_error}")
                return Response(
                    {'error': f'Erro ao baixar PDF: {str(pdf_error)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Erro ao baixar PDF: {e}")
            return Response(
                {'error': f'Erro interno: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Atualizar status do pagamento consultando Asaas"""
        try:
            payment = self.get_object()
            
            logger.info(f"🔄 Botão Atualizar Status clicado para pagamento {payment.asaas_id}")
            logger.info(f"   - Status atual: {payment.status}")
            logger.info(f"   - External Reference: {payment.external_reference}")
            
            if not payment.asaas_id:
                return Response(
                    {'error': 'Pagamento não possui ID do Asaas'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not AsaasClient:
                return Response(
                    {'error': 'Serviço Asaas não disponível'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Obter configuração
            config = AsaasConfig.get_config()
            if not config or not config.api_key:
                return Response(
                    {'error': 'Asaas não configurado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Consultar status no Asaas
            client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
            result = client.get_payment(payment.asaas_id)
            
            if result:
                # Atualizar status local
                old_status = payment.status
                payment.status = result.get('status', payment.status)
                
                logger.info(f"   - Status no Asaas: {payment.status}")
                
                # Atualizar data de pagamento se foi pago
                if payment.status in ['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']:
                    payment.payment_date = result.get('paymentDate')
                
                payment.save()
                
                # Se o pagamento foi confirmado, atualizar financeiro e criar próximo boleto
                loja_updated = False
                if payment.status in ['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']:
                    logger.info("   - Pagamento está PAGO, iniciando atualização do financeiro...")
                    try:
                        from superadmin.sync_service import AsaasSyncService
                        sync_service = AsaasSyncService()
                        loja_updated = sync_service._update_loja_financeiro_from_payment(payment)
                        logger.info(f"   - Resultado da atualização: {loja_updated}")
                        
                        if loja_updated:
                            logger.info("✅ Financeiro da loja atualizado com sucesso via botão Atualizar Status")
                        else:
                            logger.warning("⚠️ Financeiro da loja NÃO foi atualizado (retornou False)")
                    except Exception as e:
                        logger.error(f"❌ Erro ao atualizar financeiro da loja: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    logger.info(f"   - Pagamento NÃO está pago (status: {payment.status}), pulando atualização")
                
                return Response({
                    'success': True,
                    'message': 'Status atualizado com sucesso',
                    'old_status': old_status,
                    'new_status': payment.status,
                    'status_display': payment.get_status_display(),
                    'loja_updated': loja_updated
                })
            else:
                return Response(
                    {'error': 'Não foi possível consultar o status no Asaas'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar status: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Erro interno: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['delete'])
    def delete_payment(self, request, pk=None):
        """Excluir cobrança no Asaas e no sistema"""
        try:
            payment = self.get_object()
            
            logger.info(f"🗑️ Excluindo cobrança {payment.asaas_id}")
            logger.info(f"   - Status: {payment.status}")
            logger.info(f"   - Valor: R$ {payment.value}")
            
            # Validar se pode excluir
            if payment.status in ['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']:
                return Response(
                    {'error': 'Não é possível excluir uma cobrança já paga'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not payment.asaas_id:
                return Response(
                    {'error': 'Pagamento não possui ID do Asaas'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not AsaasClient:
                return Response(
                    {'error': 'Serviço Asaas não disponível'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Obter configuração
            config = AsaasConfig.get_config()
            if not config or not config.api_key:
                return Response(
                    {'error': 'Asaas não configurado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Excluir no Asaas
            client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
            try:
                client.delete_payment(payment.asaas_id)
                logger.info("✅ Cobrança excluída no Asaas")
            except Exception as e:
                logger.error(f"❌ Erro ao excluir no Asaas: {e}")
                return Response(
                    {'error': f'Erro ao excluir no Asaas: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Excluir localmente
            payment_id = payment.id
            payment.delete()
            logger.info(f"✅ Cobrança excluída localmente (ID: {payment_id})")
            
            return Response({
                'success': True,
                'message': 'Cobrança excluída com sucesso'
            })
                
        except Exception as e:
            logger.error(f"❌ Erro ao excluir cobrança: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Erro interno: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
