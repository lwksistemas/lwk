"""Estatísticas e sincronização Asaas."""
import logging
from datetime import timedelta

from django.db.models import F, Sum
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from ..models import AsaasCustomer, AsaasPayment, LojaAssinatura
from ._common import IsSuperAdmin, REQUESTS_AVAILABLE

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def asaas_stats(request):
    """Estatísticas da integração Asaas"""
    
    try:
        # Estatísticas dos clientes
        total_customers = AsaasCustomer.objects.count()
        
        # Estatísticas dos pagamentos
        total_payments = AsaasPayment.objects.count()
        pending_payments = AsaasPayment.objects.filter(status='PENDING').count()
        confirmed_payments = AsaasPayment.objects.filter(
            status__in=['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']
        ).count()
        
        # Receita total (apenas pagamentos confirmados)
        total_revenue = AsaasPayment.objects.filter(
            status__in=['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']
        ).aggregate(total=Sum('value'))['total'] or 0
        
        # Último pagamento
        last_payment = AsaasPayment.objects.order_by('-created_at').first()
        last_payment_date = last_payment.created_at.isoformat() if last_payment else None
        
        # Estatísticas por período (últimos 30 dias)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_payments = AsaasPayment.objects.filter(created_at__gte=thirty_days_ago)
        recent_revenue = recent_payments.filter(
            status__in=['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']
        ).aggregate(total=Sum('value'))['total'] or 0
        
        return Response({
            'total_customers': total_customers,
            'total_payments': total_payments,
            'pending_payments': pending_payments,
            'confirmed_payments': confirmed_payments,
            'total_revenue': float(total_revenue),
            'last_payment_date': last_payment_date,
            'recent_revenue_30d': float(recent_revenue),
            'recent_payments_30d': recent_payments.count()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas Asaas: {e}")
        return Response(
            {'detail': f'Erro ao obter estatísticas: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def asaas_sync(request):
    """Sincronização manual de pagamentos"""
    try:
        from superadmin.sync_service import AsaasSyncService
        
        sync_service = AsaasSyncService()
        loja_slug = request.data.get('loja')
        
        if loja_slug:
            # Sincronizar loja específica
            try:
                from superadmin.models import Loja
                loja = Loja.objects.get(slug=loja_slug, is_active=True)
                resultado = sync_service.sync_loja_payments(loja)
            except Loja.DoesNotExist:
                return Response({
                    'success': False,
                    'error': f'Loja "{loja_slug}" não encontrada'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # Sincronizar todas as lojas
            resultado = sync_service.sync_all_payments()
        
        return Response(resultado)
        
    except ImportError:
        return Response({
            'success': False,
            'error': 'Serviço de sincronização não disponível'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Erro na sincronização manual: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def asaas_sync_stats(request):
    """Estatísticas de sincronização"""
    try:
        from superadmin.sync_service import AsaasSyncService
        
        sync_service = AsaasSyncService()
        stats = sync_service.get_sync_stats()
        
        return Response(stats)
        
    except ImportError:
        return Response({
            'error': 'Serviço de sincronização não disponível'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def asaas_sync_realtime(request):
    """Sincronização em tempo real de pagamentos específicos"""
    try:
        from superadmin.sync_service import AsaasSyncService
        
        sync_service = AsaasSyncService()
        
        # Pegar parâmetros da requisição
        payment_id = request.data.get('payment_id')
        loja_slug = request.data.get('loja_slug')
        
        if payment_id:
            # Sincronizar pagamento específico
            try:
                from asaas_integration.models import AsaasPayment
                from superadmin.models import PagamentoLoja
                
                # Buscar pagamento
                pagamento = None
                try:
                    pagamento = AsaasPayment.objects.get(asaas_id=payment_id)
                except AsaasPayment.DoesNotExist:
                    try:
                        pagamento = PagamentoLoja.objects.get(asaas_payment_id=payment_id)
                    except PagamentoLoja.DoesNotExist:
                        return Response({
                            'success': False,
                            'error': f'Pagamento {payment_id} não encontrado'
                        }, status=status.HTTP_404_NOT_FOUND)
                
                # Consultar status atual no Asaas
                resultado = sync_service.sync_payment_status(pagamento)
                
                return Response({
                    'success': True,
                    'payment_id': payment_id,
                    'sync_result': resultado
                })
                
            except Exception as e:
                return Response({
                    'success': False,
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        elif loja_slug:
            # Sincronizar loja específica
            try:
                from superadmin.models import Loja
                loja = Loja.objects.get(slug=loja_slug, is_active=True)
                resultado = sync_service.sync_loja_payments(loja)
                return Response(resultado)
            except Loja.DoesNotExist:
                return Response({
                    'success': False,
                    'error': f'Loja "{loja_slug}" não encontrada'
                }, status=status.HTTP_404_NOT_FOUND)
        
        else:
            return Response({
                'success': False,
                'error': 'payment_id ou loja_slug é obrigatório'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Erro na sincronização em tempo real: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


