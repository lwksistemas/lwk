"""
Views para integração com Asaas
Gerencia configurações, monitoramento e sincronização
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, Count
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from datetime import datetime, timedelta
import os
import logging

# Importações condicionais para evitar erros na inicialização
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from .models import AsaasCustomer, AsaasPayment, LojaAssinatura
from superadmin.models import Loja

logger = logging.getLogger(__name__)

class IsSuperAdmin(permissions.BasePermission):
    """Permissão apenas para super admins"""
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser

# Importação condicional do cliente Asaas
if REQUESTS_AVAILABLE:
    try:
        from .client import AsaasClient
    except ImportError:
        AsaasClient = None
else:
    AsaasClient = None

class IsSuperAdmin(permissions.BasePermission):
    """Permissão apenas para super admins"""
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser

@api_view(['GET', 'POST'])
@permission_classes([IsSuperAdmin])
def asaas_config(request):
    """Gerenciar configurações do Asaas"""
    
    if not REQUESTS_AVAILABLE:
        return Response(
            {'detail': 'Biblioteca requests não disponível. Instale com: pip install requests'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    if request.method == 'GET':
        # Retornar configurações atuais (sem expor a chave completa)
        api_key = os.environ.get('ASAAS_API_KEY', '')
        masked_key = f"{api_key[:10]}...{api_key[-4:]}" if len(api_key) > 14 else api_key
        
        return Response({
            'api_key': masked_key,
            'sandbox': os.environ.get('ASAAS_SANDBOX', 'True').lower() in ['true', '1', 'yes', 'on'],
            'enabled': getattr(settings, 'ASAAS_INTEGRATION_ENABLED', False),
            'last_sync': get_last_sync_time()
        })
    
    elif request.method == 'POST':
        # Salvar novas configurações
        api_key = request.data.get('api_key', '').strip()
        sandbox = request.data.get('sandbox', True)
        enabled = request.data.get('enabled', False)
        
        if not api_key:
            return Response(
                {'detail': 'Chave da API é obrigatória'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar formato da chave (aceitar tanto sandbox quanto produção)
        if not api_key.startswith('$aact_'):
            return Response(
                {'detail': 'Formato da chave API inválido. Deve começar com $aact_'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Detectar automaticamente se é sandbox ou produção
        is_sandbox_key = 'hmlg' in api_key
        if is_sandbox_key and not sandbox:
            return Response(
                {'detail': 'Esta é uma chave de SANDBOX. Selecione "Sandbox" como ambiente.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif not is_sandbox_key and sandbox:
            return Response(
                {'detail': 'Esta é uma chave de PRODUÇÃO. Selecione "Produção" como ambiente.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Salvar configuração sem validar (validação será feita no teste)
        try:
            # Atualizar variáveis de ambiente (temporariamente)
            os.environ['ASAAS_API_KEY'] = api_key
            os.environ['ASAAS_SANDBOX'] = str(sandbox)
            
            # Atualizar configurações do Django
            settings.ASAAS_API_KEY = api_key
            settings.ASAAS_SANDBOX = sandbox
            settings.ASAAS_INTEGRATION_ENABLED = enabled
            
            return Response({
                'message': 'Configuração salva com sucesso. Use "Testar Conexão" para validar a chave.',
                'api_key': f"{api_key[:10]}...{api_key[-4:]}",
                'sandbox': sandbox,
                'enabled': enabled
            })
            
        except Exception as e:
            return Response(
                {'detail': f'Erro ao salvar configuração: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def asaas_test(request):
    """Testar conexão com a API do Asaas"""
    
    if not REQUESTS_AVAILABLE or not AsaasClient:
        return Response(
            {'detail': 'Biblioteca requests não disponível. Instale com: pip install requests'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        api_key = os.environ.get('ASAAS_API_KEY')
        if not api_key:
            return Response(
                {'detail': 'Chave da API não configurada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sandbox_env = os.environ.get('ASAAS_SANDBOX', 'True')
        is_sandbox = sandbox_env.lower() in ['true', '1', 'yes', 'on']
        client = AsaasClient(api_key=api_key, sandbox=is_sandbox)
        
        # Testar com uma requisição simples
        result = client._make_request('GET', 'customers?limit=1')
        
        return Response({
            'message': 'Conexão testada com sucesso',
            'environment': 'Sandbox' if is_sandbox else 'Produção',
            'api_status': 'Conectado',
            'test_time': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao testar API Asaas: {e}")
        return Response(
            {'detail': f'Erro na conexão: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def asaas_status(request):
    """Status atual da integração Asaas"""
    
    try:
        api_key = os.environ.get('ASAAS_API_KEY')
        sandbox_env = os.environ.get('ASAAS_SANDBOX', 'True')
        is_sandbox = sandbox_env.lower() in ['true', '1', 'yes', 'on']
        enabled = getattr(settings, 'ASAAS_INTEGRATION_ENABLED', False)
        
        api_connected = False
        error_message = None
        
        if not REQUESTS_AVAILABLE:
            error_message = 'Biblioteca requests não disponível'
        elif api_key and enabled and AsaasClient:
            try:
                client = AsaasClient(api_key=api_key, sandbox=is_sandbox)
                client._make_request('GET', 'customers?limit=1')
                api_connected = True
            except Exception as e:
                error_message = str(e)
        elif not api_key:
            error_message = 'Chave da API não configurada'
        elif not enabled:
            error_message = 'Integração desabilitada'
        
        return Response({
            'api_connected': api_connected,
            'last_check': timezone.now().isoformat(),
            'error_message': error_message,
            'environment': 'Sandbox' if is_sandbox else 'Produção',
            'enabled': enabled,
            'requests_available': REQUESTS_AVAILABLE
        })
        
    except Exception as e:
        return Response(
            {'detail': f'Erro ao verificar status: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

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
    """Sincronizar pagamentos com a API do Asaas"""
    
    try:
        api_key = os.environ.get('ASAAS_API_KEY')
        if not api_key:
            return Response(
                {'detail': 'Chave da API não configurada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sandbox_env = os.environ.get('ASAAS_SANDBOX', 'True')
        is_sandbox = sandbox_env.lower() in ['true', '1', 'yes', 'on']
        client = AsaasClient(api_key=api_key, sandbox=is_sandbox)
        
        synced_count = 0
        errors = []
        
        # Buscar todos os pagamentos do Asaas
        try:
            payments_response = client._make_request('GET', 'payments?limit=100')
            payments = payments_response.get('data', [])
            
            for payment_data in payments:
                try:
                    # Verificar se o pagamento já existe
                    asaas_id = payment_data['id']
                    
                    payment, created = AsaasPayment.objects.get_or_create(
                        asaas_id=asaas_id,
                        defaults={
                            'billing_type': payment_data.get('billingType', 'UNDEFINED'),
                            'status': payment_data.get('status', 'PENDING'),
                            'value': payment_data.get('value', 0),
                            'due_date': payment_data.get('dueDate'),
                            'description': payment_data.get('description', ''),
                            'external_reference': payment_data.get('externalReference', ''),
                            'raw_data': payment_data
                        }
                    )
                    
                    if created:
                        synced_count += 1
                        
                        # Tentar associar com cliente
                        customer_id = payment_data.get('customer')
                        if customer_id:
                            try:
                                customer = AsaasCustomer.objects.get(asaas_id=customer_id)
                                payment.customer = customer
                                payment.save()
                            except AsaasCustomer.DoesNotExist:
                                # Cliente não existe, buscar na API
                                try:
                                    customer_data = client._make_request('GET', f'customers/{customer_id}')
                                    customer = AsaasCustomer.objects.create(
                                        asaas_id=customer_id,
                                        name=customer_data.get('name', ''),
                                        email=customer_data.get('email', ''),
                                        cpf_cnpj=customer_data.get('cpfCnpj', ''),
                                        raw_data=customer_data
                                    )
                                    payment.customer = customer
                                    payment.save()
                                except Exception as e:
                                    errors.append(f"Erro ao criar cliente {customer_id}: {str(e)}")
                    else:
                        # Atualizar status se mudou
                        if payment.status != payment_data.get('status'):
                            payment.status = payment_data.get('status', 'PENDING')
                            payment.raw_data = payment_data
                            payment.save()
                            synced_count += 1
                
                except Exception as e:
                    errors.append(f"Erro ao processar pagamento {payment_data.get('id', 'unknown')}: {str(e)}")
                    
        except Exception as e:
            return Response(
                {'detail': f'Erro ao buscar pagamentos: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Atualizar timestamp da última sincronização
        set_last_sync_time()
        
        response_data = {
            'message': 'Sincronização concluída',
            'synced_count': synced_count,
            'total_payments': AsaasPayment.objects.count(),
            'sync_time': timezone.now().isoformat()
        }
        
        if errors:
            response_data['errors'] = errors[:10]  # Limitar a 10 erros
            response_data['total_errors'] = len(errors)
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Erro na sincronização Asaas: {e}")
        return Response(
            {'detail': f'Erro na sincronização: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def get_last_sync_time():
    """Obter timestamp da última sincronização"""
    try:
        # Buscar o pagamento mais recente como proxy para última sync
        last_payment = AsaasPayment.objects.order_by('-updated_at').first()
        return last_payment.updated_at.isoformat() if last_payment else None
    except:
        return None

@csrf_exempt
@api_view(['POST'])
@permission_classes([])  # Webhook público, sem autenticação
def asaas_webhook(request):
    """Webhook para receber notificações do Asaas"""
    
    try:
        # Log da requisição para debug
        logger.info(f"Webhook Asaas recebido: {request.data}")
        
        # Verificar se é uma notificação de pagamento
        event_type = request.data.get('event')
        payment_data = request.data.get('payment', {})
        
        if not event_type or not payment_data:
            return Response({'status': 'ignored'}, status=status.HTTP_200_OK)
        
        # Processar apenas eventos de pagamento
        if event_type in ['PAYMENT_CREATED', 'PAYMENT_UPDATED', 'PAYMENT_CONFIRMED', 'PAYMENT_RECEIVED']:
            payment_id = payment_data.get('id')
            
            if payment_id:
                # Buscar ou criar o pagamento
                payment, created = AsaasPayment.objects.get_or_create(
                    asaas_id=payment_id,
                    defaults={
                        'billing_type': payment_data.get('billingType', 'UNDEFINED'),
                        'status': payment_data.get('status', 'PENDING'),
                        'value': payment_data.get('value', 0),
                        'due_date': payment_data.get('dueDate'),
                        'description': payment_data.get('description', ''),
                        'external_reference': payment_data.get('externalReference', ''),
                        'raw_data': payment_data
                    }
                )
                
                # Atualizar se já existia
                if not created:
                    payment.status = payment_data.get('status', payment.status)
                    payment.raw_data = payment_data
                    if payment_data.get('paymentDate'):
                        payment.payment_date = payment_data.get('paymentDate')
                    payment.save()
                
                # Buscar e associar cliente se necessário
                customer_id = payment_data.get('customer')
                if customer_id and not payment.customer:
                    try:
                        customer = AsaasCustomer.objects.get(asaas_id=customer_id)
                        payment.customer = customer
                        payment.save()
                    except AsaasCustomer.DoesNotExist:
                        # Cliente será criado na próxima sincronização
                        pass
                
                logger.info(f"Pagamento {payment_id} processado via webhook: {event_type}")
                
                return Response({
                    'status': 'processed',
                    'event': event_type,
                    'payment_id': payment_id
                }, status=status.HTTP_200_OK)
        
        return Response({'status': 'ignored'}, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erro no webhook Asaas: {e}")
        # Retornar 200 mesmo com erro para não reenviar o webhook
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_200_OK)


def set_last_sync_time():
    """Definir timestamp da última sincronização"""
    # Por enquanto, não fazemos nada específico
    # Podemos implementar um modelo de configuração no futuro
    pass