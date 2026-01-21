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

from .models import AsaasCustomer, AsaasPayment, LojaAssinatura, AsaasConfig
from .serializers import AsaasCustomerSerializer, AsaasPaymentSerializer, LojaAssinaturaSerializer
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
        # Retornar configurações atuais do banco de dados
        config = AsaasConfig.get_config()
        
        return Response({
            'api_key': config.api_key_masked,
            'sandbox': config.sandbox,
            'enabled': config.enabled,
            'last_sync': config.last_sync.isoformat() if config.last_sync else None
        })
    
    elif request.method == 'POST':
        # Salvar novas configurações no banco de dados
        api_key = request.data.get('api_key', '').strip()
        enabled = request.data.get('enabled', False)
        
        if not api_key:
            return Response(
                {'detail': 'Chave da API é obrigatória'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar formato da chave
        if not api_key.startswith('$aact_'):
            return Response(
                {'detail': 'Formato da chave API inválido. Deve começar com $aact_'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Salvar configuração no banco
        try:
            config = AsaasConfig.get_config()
            config.api_key = api_key
            config.enabled = enabled
            config.save()  # O sandbox será detectado automaticamente no save()
            
            return Response({
                'message': 'Configuração salva com sucesso no banco de dados.',
                'api_key': config.api_key_masked,
                'sandbox': config.sandbox,
                'enabled': config.enabled
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
        config = AsaasConfig.get_config()
        if not config.api_key:
            return Response(
                {'detail': 'Chave da API não configurada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
        
        # Testar com uma requisição simples
        result = client._make_request('GET', 'customers?limit=1')
        
        return Response({
            'message': 'Conexão testada com sucesso',
            'environment': config.environment_name,
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
        config = AsaasConfig.get_config()
        
        api_connected = False
        error_message = None
        
        if not REQUESTS_AVAILABLE:
            error_message = 'Biblioteca requests não disponível'
        elif config.api_key and config.enabled and AsaasClient:
            try:
                client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
                client._make_request('GET', 'customers?limit=1')
                api_connected = True
            except Exception as e:
                error_message = str(e)
        elif not config.api_key:
            error_message = 'Chave da API não configurada'
        elif not config.enabled:
            error_message = 'Integração desabilitada'
        
        return Response({
            'api_connected': api_connected,
            'last_check': timezone.now().isoformat(),
            'error_message': error_message,
            'environment': config.environment_name,
            'enabled': config.enabled,
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
        
        # Processar apenas eventos de pagamento relevantes
        if event_type in ['PAYMENT_CREATED', 'PAYMENT_UPDATED', 'PAYMENT_CONFIRMED', 'PAYMENT_RECEIVED']:
            
            # Usar o novo serviço de sincronização
            try:
                from superadmin.sync_service import AsaasSyncService
                
                sync_service = AsaasSyncService()
                resultado = sync_service.process_webhook_payment(payment_data)
                
                if resultado['success']:
                    logger.info(f"Webhook processado com sucesso: {resultado}")
                    
                    response_data = {
                        'status': 'processed',
                        'payment_id': resultado.get('payment_id'),
                        'status_updated': resultado.get('status_updated', False)
                    }
                    
                    # Adicionar informações sobre bloqueio/desbloqueio
                    if resultado.get('blocked'):
                        response_data['loja_blocked'] = True
                        logger.warning(f"Loja bloqueada via webhook: {resultado.get('payment_id')}")
                    
                    if resultado.get('unblocked'):
                        response_data['loja_unblocked'] = True
                        logger.info(f"Loja desbloqueada via webhook: {resultado.get('payment_id')}")
                    
                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    logger.error(f"Erro ao processar webhook: {resultado.get('error')}")
                    return Response({
                        'status': 'error',
                        'error': resultado.get('error')
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except ImportError:
                logger.error("Serviço de sincronização não disponível")
                return Response({
                    'status': 'error',
                    'error': 'Serviço de sincronização não disponível'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Evento não processado
        return Response({'status': 'ignored'}, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erro no webhook Asaas: {e}")
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({'status': 'ignored'}, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erro no webhook Asaas: {e}")
        # Retornar 200 mesmo com erro para não reenviar o webhook
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
@permission_classes([])  # Endpoint público para teste
def asaas_test_public(request):
    """Testar conexão com a API do Asaas - endpoint público para debug"""
    
    if not REQUESTS_AVAILABLE or not AsaasClient:
        return Response(
            {'detail': 'Biblioteca requests não disponível. Instale com: pip install requests'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        # Pegar chave da requisição
        api_key = request.data.get('api_key')
        if not api_key:
            return Response(
                {'detail': 'Chave da API é obrigatória no body da requisição'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Auto-detectar sandbox baseado na chave
        is_sandbox = 'hmlg' in api_key
        client = AsaasClient(api_key=api_key, sandbox=is_sandbox)
        
        # Testar com uma requisição simples
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

def set_last_sync_time():
    """Definir timestamp da última sincronização"""
    try:
        config = AsaasConfig.get_config()
        config.last_sync = timezone.now()
        config.save()
    except Exception as e:
        logger.error(f"Erro ao salvar timestamp de sincronização: {e}")

def get_last_sync_time():
    """Obter timestamp da última sincronização"""
    try:
        config = AsaasConfig.get_config()
        return config.last_sync.isoformat() if config.last_sync else None
    except Exception as e:
        logger.error(f"Erro ao obter timestamp de sincronização: {e}")
        return None


# ViewSets para API REST

class AsaasSubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para assinaturas Asaas (somente leitura para superadmin)"""
    serializer_class = LojaAssinaturaSerializer
    permission_classes = [IsSuperAdmin]
    queryset = LojaAssinatura.objects.all().select_related('asaas_customer', 'current_payment')
    
    def get_queryset(self):
        """Filtrar assinaturas com ordenação"""
        queryset = super().get_queryset()
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Estatísticas para dashboard financeiro"""
        try:
            # Estatísticas das assinaturas
            total_assinaturas = LojaAssinatura.objects.count()
            assinaturas_ativas = LojaAssinatura.objects.filter(ativa=True).count()
            
            # Estatísticas dos pagamentos
            total_pagamentos = AsaasPayment.objects.count()
            pagamentos_pendentes = AsaasPayment.objects.filter(status='PENDING').count()
            pagamentos_pagos = AsaasPayment.objects.filter(
                status__in=['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']
            ).count()
            pagamentos_vencidos = AsaasPayment.objects.filter(status='OVERDUE').count()
            
            # Receita total e pendente
            receita_total = AsaasPayment.objects.filter(
                status__in=['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']
            ).aggregate(total=Sum('value'))['total'] or 0
            
            receita_pendente = AsaasPayment.objects.filter(
                status__in=['PENDING', 'OVERDUE']
            ).aggregate(total=Sum('value'))['total'] or 0
            
            return Response({
                'total_assinaturas': total_assinaturas,
                'assinaturas_ativas': assinaturas_ativas,
                'pagamentos_pendentes': pagamentos_pendentes,
                'pagamentos_pagos': pagamentos_pagos,
                'pagamentos_vencidos': pagamentos_vencidos,
                'receita_total': float(receita_total),
                'receita_pendente': float(receita_pendente)
            })
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return Response(
                {'error': f'Erro interno: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def generate_new_payment(self, request, pk=None):
        """Gerar nova cobrança para assinatura"""
        try:
            assinatura = self.get_object()
            
            # Importar serviço de pagamento
            if not AsaasClient:
                return Response(
                    {'error': 'Serviço Asaas não disponível'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            from .client import AsaasPaymentService
            service = AsaasPaymentService()
            
            # Dados da loja
            loja = Loja.objects.select_related('owner').get(slug=assinatura.loja_slug)
            
            loja_data = {
                'nome': loja.nome,
                'slug': loja.slug,
                'email': loja.owner.email,
                'cpf_cnpj': loja.cpf_cnpj,
                'telefone': getattr(loja.owner, 'telefone', ''),
                'endereco': getattr(loja, 'endereco', ''),
                'cidade': getattr(loja, 'cidade', ''),
                'estado': getattr(loja, 'estado', ''),
                'cep': getattr(loja, 'cep', '')
            }
            
            plano_data = {
                'nome': assinatura.plano_nome,
                'preco': float(assinatura.plano_valor)
            }
            
            # Criar nova cobrança
            resultado = service.create_loja_subscription_payment(loja_data, plano_data)
            
            if resultado.get('success'):
                return Response({
                    'success': True,
                    'message': 'Nova cobrança gerada com sucesso',
                    'payment_id': resultado.get('payment_id')
                })
            else:
                return Response(
                    {'error': resultado.get('error', 'Erro ao gerar cobrança')},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Erro ao gerar nova cobrança: {e}")
            return Response(
                {'error': f'Erro interno: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )


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
                
                # Atualizar data de pagamento se foi pago
                if payment.status in ['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']:
                    payment.payment_date = result.get('paymentDate')
                
                payment.save()
                
                return Response({
                    'success': True,
                    'message': 'Status atualizado com sucesso',
                    'old_status': old_status,
                    'new_status': payment.status,
                    'status_display': payment.get_status_display()
                })
            else:
                return Response(
                    {'error': 'Não foi possível consultar o status no Asaas'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Erro ao atualizar status: {e}")
            return Response(
                {'error': f'Erro interno: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )