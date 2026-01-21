# Exemplo de Implementação - Mercado Pago Integration

## Estrutura do Módulo

```
backend/mercadopago_integration/
├── __init__.py
├── apps.py
├── models.py
├── client.py
├── serializers.py
├── views.py
├── urls.py
├── admin.py
├── signals.py
└── migrations/
    └── 0001_initial.py
```

## Modelos de Dados

```python
# backend/mercadopago_integration/models.py
from django.db import models
from django.utils import timezone

class MercadoPagoConfig(models.Model):
    """Configuração global do Mercado Pago"""
    access_token = models.TextField(help_text="Access Token do Mercado Pago")
    public_key = models.CharField(max_length=200, help_text="Public Key do Mercado Pago")
    sandbox = models.BooleanField(default=True)
    enabled = models.BooleanField(default=True)
    webhook_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuração Mercado Pago"
        verbose_name_plural = "Configurações Mercado Pago"
    
    @classmethod
    def get_config(cls):
        config, created = cls.objects.get_or_create(id=1)
        return config
    
    @property
    def access_token_masked(self):
        if self.access_token:
            return f"{self.access_token[:10]}...{self.access_token[-4:]}"
        return "Não configurado"
    
    @property
    def environment_name(self):
        return "Sandbox" if self.sandbox else "Produção"

class MercadoPagoCustomer(models.Model):
    """Cliente no Mercado Pago"""
    mp_id = models.CharField(max_length=100, unique=True)
    email = models.EmailField()
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    identification_type = models.CharField(max_length=10)  # CPF, CNPJ
    identification_number = models.CharField(max_length=20)
    phone = models.CharField(max_length=20, blank=True)
    address = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Cliente Mercado Pago"
        verbose_name_plural = "Clientes Mercado Pago"
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.mp_id})"

class MercadoPagoPayment(models.Model):
    """Pagamento no Mercado Pago"""
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('approved', 'Aprovado'),
        ('authorized', 'Autorizado'),
        ('in_process', 'Em Processamento'),
        ('in_mediation', 'Em Mediação'),
        ('rejected', 'Rejeitado'),
        ('cancelled', 'Cancelado'),
        ('refunded', 'Reembolsado'),
        ('charged_back', 'Chargeback'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('pix', 'PIX'),
        ('bolbradesco', 'Boleto Bradesco'),
        ('account_money', 'Dinheiro em Conta'),
        ('credit_card', 'Cartão de Crédito'),
        ('debit_card', 'Cartão de Débito'),
    ]
    
    mp_id = models.CharField(max_length=100, unique=True)
    customer = models.ForeignKey(MercadoPagoCustomer, on_delete=models.CASCADE, related_name='payments')
    external_reference = models.CharField(max_length=200, blank=True)
    
    # Dados do pagamento
    transaction_amount = models.DecimalField(max_digits=10, decimal_places=2)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    payment_method_id = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    payment_type_id = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    status_detail = models.CharField(max_length=100, blank=True)
    
    # Datas
    date_created = models.DateTimeField()
    date_approved = models.DateTimeField(null=True, blank=True)
    date_last_updated = models.DateTimeField()
    
    # URLs e dados específicos
    transaction_details = models.JSONField(default=dict, blank=True)
    point_of_interaction = models.JSONField(default=dict, blank=True)  # QR Code, Boleto URL
    
    # Metadados
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Pagamento Mercado Pago"
        verbose_name_plural = "Pagamentos Mercado Pago"
        ordering = ['-date_created']
    
    def __str__(self):
        return f"Pagamento {self.mp_id} - {self.get_status_display()}"
    
    @property
    def is_paid(self):
        return self.status in ['approved', 'authorized']
    
    @property
    def boleto_url(self):
        """URL do boleto se disponível"""
        if self.payment_method_id.startswith('bol'):
            return self.transaction_details.get('external_resource_url')
        return None
    
    @property
    def pix_qr_code(self):
        """QR Code do PIX se disponível"""
        if self.payment_method_id == 'pix':
            return self.point_of_interaction.get('transaction_data', {}).get('qr_code')
        return None
    
    @property
    def pix_qr_code_base64(self):
        """QR Code do PIX em base64 se disponível"""
        if self.payment_method_id == 'pix':
            return self.point_of_interaction.get('transaction_data', {}).get('qr_code_base64')
        return None

class LojaSubscriptionMP(models.Model):
    """Assinatura de loja no Mercado Pago"""
    loja_slug = models.CharField(max_length=100, unique=True)
    customer = models.ForeignKey(MercadoPagoCustomer, on_delete=models.CASCADE)
    current_payment = models.ForeignKey(MercadoPagoPayment, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Dados do plano
    plan_name = models.CharField(max_length=100)
    plan_amount = models.DecimalField(max_digits=10, decimal_places=2)
    billing_cycle = models.CharField(max_length=20, default='monthly')
    
    # Status
    active = models.BooleanField(default=True)
    next_billing_date = models.DateField(null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Assinatura Loja MP"
        verbose_name_plural = "Assinaturas Loja MP"
    
    def __str__(self):
        return f"Assinatura {self.loja_slug} - {self.plan_name}"
```

## Cliente da API

```python
# backend/mercadopago_integration/client.py
import requests
import logging
from decimal import Decimal
from datetime import datetime, timedelta
from django.conf import settings
from .models import MercadoPagoConfig

logger = logging.getLogger(__name__)

class MercadoPagoClient:
    """Cliente para API do Mercado Pago"""
    
    def __init__(self, access_token=None, sandbox=True):
        config = MercadoPagoConfig.get_config()
        
        self.access_token = access_token or config.access_token
        self.sandbox = sandbox if access_token else config.sandbox
        
        if self.sandbox:
            self.base_url = "https://api.mercadopago.com"
        else:
            self.base_url = "https://api.mercadopago.com"
        
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Idempotency-Key': None  # Será definido por requisição
        }
    
    def _make_request(self, method, endpoint, data=None, idempotency_key=None):
        """Fazer requisição para API"""
        url = f"{self.base_url}/{endpoint}"
        
        headers = self.headers.copy()
        if idempotency_key:
            headers['X-Idempotency-Key'] = idempotency_key
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição Mercado Pago: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise
    
    def create_customer(self, customer_data):
        """Criar cliente"""
        endpoint = "v1/customers"
        return self._make_request('POST', endpoint, customer_data)
    
    def get_customer(self, customer_id):
        """Buscar cliente"""
        endpoint = f"v1/customers/{customer_id}"
        return self._make_request('GET', endpoint)
    
    def create_payment(self, payment_data, idempotency_key=None):
        """Criar pagamento"""
        endpoint = "v1/payments"
        return self._make_request('POST', endpoint, payment_data, idempotency_key)
    
    def get_payment(self, payment_id):
        """Buscar pagamento"""
        endpoint = f"v1/payments/{payment_id}"
        return self._make_request('GET', endpoint)
    
    def cancel_payment(self, payment_id):
        """Cancelar pagamento"""
        endpoint = f"v1/payments/{payment_id}"
        data = {"status": "cancelled"}
        return self._make_request('PUT', endpoint, data)
    
    def search_payments(self, filters):
        """Buscar pagamentos com filtros"""
        endpoint = "v1/payments/search"
        return self._make_request('GET', endpoint, filters)

class MercadoPagoPaymentService:
    """Serviço para gerenciar pagamentos"""
    
    def __init__(self):
        self.client = MercadoPagoClient()
    
    def create_loja_subscription_payment(self, loja_data, plan_data):
        """Criar pagamento de assinatura para loja"""
        try:
            # 1. Criar ou buscar cliente
            customer = self._get_or_create_customer(loja_data)
            
            # 2. Criar pagamento
            payment_data = {
                "transaction_amount": float(plan_data['preco']),
                "description": f"Assinatura {plan_data['nome']} - Loja {loja_data['nome']}",
                "payment_method_id": "bolbradesco",  # Padrão boleto
                "payer": {
                    "id": customer.mp_id,
                    "email": loja_data['email'],
                    "first_name": loja_data['nome'].split()[0],
                    "last_name": " ".join(loja_data['nome'].split()[1:]) or "Loja",
                    "identification": {
                        "type": "CPF" if len(loja_data['cpf_cnpj']) == 11 else "CNPJ",
                        "number": loja_data['cpf_cnpj']
                    }
                },
                "external_reference": f"loja_{loja_data['slug']}_assinatura",
                "date_of_expiration": (datetime.now() + timedelta(days=7)).isoformat(),
                "metadata": {
                    "loja_slug": loja_data['slug'],
                    "plan_name": plan_data['nome']
                }
            }
            
            # Gerar chave de idempotência
            idempotency_key = f"loja_{loja_data['slug']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            result = self.client.create_payment(payment_data, idempotency_key)
            
            # 3. Salvar pagamento local
            payment = self._save_payment(result, customer)
            
            # 4. Criar ou atualizar assinatura
            self._update_subscription(loja_data['slug'], customer, payment, plan_data)
            
            return {
                'success': True,
                'payment_id': result['id'],
                'boleto_url': result.get('transaction_details', {}).get('external_resource_url'),
                'due_date': result.get('date_of_expiration'),
                'amount': result['transaction_amount']
            }
            
        except Exception as e:
            logger.error(f"Erro ao criar pagamento MP: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_pix_payment(self, loja_data, plan_data):
        """Criar pagamento PIX"""
        try:
            customer = self._get_or_create_customer(loja_data)
            
            payment_data = {
                "transaction_amount": float(plan_data['preco']),
                "description": f"Assinatura {plan_data['nome']} - Loja {loja_data['nome']}",
                "payment_method_id": "pix",
                "payer": {
                    "email": loja_data['email'],
                    "first_name": loja_data['nome'].split()[0],
                    "last_name": " ".join(loja_data['nome'].split()[1:]) or "Loja",
                    "identification": {
                        "type": "CPF" if len(loja_data['cpf_cnpj']) == 11 else "CNPJ",
                        "number": loja_data['cpf_cnpj']
                    }
                },
                "external_reference": f"loja_{loja_data['slug']}_pix",
                "date_of_expiration": (datetime.now() + timedelta(hours=24)).isoformat()
            }
            
            result = self.client.create_payment(payment_data)
            payment = self._save_payment(result, customer)
            
            return {
                'success': True,
                'payment_id': result['id'],
                'qr_code': result.get('point_of_interaction', {}).get('transaction_data', {}).get('qr_code'),
                'qr_code_base64': result.get('point_of_interaction', {}).get('transaction_data', {}).get('qr_code_base64'),
                'amount': result['transaction_amount']
            }
            
        except Exception as e:
            logger.error(f"Erro ao criar PIX MP: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_or_create_customer(self, loja_data):
        """Buscar ou criar cliente"""
        from .models import MercadoPagoCustomer
        
        # Tentar buscar por email
        try:
            return MercadoPagoCustomer.objects.get(email=loja_data['email'])
        except MercadoPagoCustomer.DoesNotExist:
            pass
        
        # Criar novo cliente
        customer_data = {
            "email": loja_data['email'],
            "first_name": loja_data['nome'].split()[0],
            "last_name": " ".join(loja_data['nome'].split()[1:]) or "Loja",
            "identification": {
                "type": "CPF" if len(loja_data['cpf_cnpj']) == 11 else "CNPJ",
                "number": loja_data['cpf_cnpj']
            },
            "phone": {
                "area_code": loja_data.get('telefone', '')[:2] or "11",
                "number": loja_data.get('telefone', '')[2:] or "999999999"
            }
        }
        
        result = self.client.create_customer(customer_data)
        
        return MercadoPagoCustomer.objects.create(
            mp_id=result['id'],
            email=result['email'],
            first_name=result['first_name'],
            last_name=result['last_name'],
            identification_type=result['identification']['type'],
            identification_number=result['identification']['number'],
            phone=f"{result.get('phone', {}).get('area_code', '')}{result.get('phone', {}).get('number', '')}"
        )
    
    def _save_payment(self, payment_data, customer):
        """Salvar pagamento no banco local"""
        from .models import MercadoPagoPayment
        
        return MercadoPagoPayment.objects.create(
            mp_id=payment_data['id'],
            customer=customer,
            external_reference=payment_data.get('external_reference', ''),
            transaction_amount=Decimal(str(payment_data['transaction_amount'])),
            net_amount=Decimal(str(payment_data.get('net_amount', 0))),
            payment_method_id=payment_data['payment_method_id'],
            payment_type_id=payment_data['payment_type_id'],
            status=payment_data['status'],
            status_detail=payment_data.get('status_detail', ''),
            date_created=datetime.fromisoformat(payment_data['date_created'].replace('Z', '+00:00')),
            date_last_updated=datetime.fromisoformat(payment_data['date_last_updated'].replace('Z', '+00:00')),
            transaction_details=payment_data.get('transaction_details', {}),
            point_of_interaction=payment_data.get('point_of_interaction', {}),
            description=payment_data.get('description', ''),
            metadata=payment_data.get('metadata', {}),
            raw_data=payment_data
        )
    
    def _update_subscription(self, loja_slug, customer, payment, plan_data):
        """Criar ou atualizar assinatura"""
        from .models import LojaSubscriptionMP
        
        subscription, created = LojaSubscriptionMP.objects.get_or_create(
            loja_slug=loja_slug,
            defaults={
                'customer': customer,
                'current_payment': payment,
                'plan_name': plan_data['nome'],
                'plan_amount': Decimal(str(plan_data['preco'])),
                'next_billing_date': (datetime.now() + timedelta(days=30)).date()
            }
        )
        
        if not created:
            subscription.current_payment = payment
            subscription.plan_name = plan_data['nome']
            subscription.plan_amount = Decimal(str(plan_data['preco']))
            subscription.save()
        
        return subscription
```

## Views da API

```python
# backend/mercadopago_integration/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging

from .models import MercadoPagoConfig, MercadoPagoPayment, LojaSubscriptionMP
from .client import MercadoPagoClient, MercadoPagoPaymentService
from .serializers import MercadoPagoPaymentSerializer, LojaSubscriptionMPSerializer

logger = logging.getLogger(__name__)

class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser

@api_view(['GET', 'POST'])
@permission_classes([IsSuperAdmin])
def mercadopago_config(request):
    """Gerenciar configurações do Mercado Pago"""
    
    if request.method == 'GET':
        config = MercadoPagoConfig.get_config()
        return Response({
            'access_token': config.access_token_masked,
            'public_key': config.public_key[:10] + '...' if config.public_key else '',
            'sandbox': config.sandbox,
            'enabled': config.enabled,
            'environment': config.environment_name
        })
    
    elif request.method == 'POST':
        access_token = request.data.get('access_token', '').strip()
        public_key = request.data.get('public_key', '').strip()
        enabled = request.data.get('enabled', False)
        
        if not access_token or not public_key:
            return Response(
                {'detail': 'Access Token e Public Key são obrigatórios'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            config = MercadoPagoConfig.get_config()
            config.access_token = access_token
            config.public_key = public_key
            config.enabled = enabled
            config.sandbox = 'TEST' in access_token  # Auto-detectar sandbox
            config.save()
            
            return Response({
                'message': 'Configuração salva com sucesso',
                'access_token': config.access_token_masked,
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
def mercadopago_test(request):
    """Testar conexão com Mercado Pago"""
    try:
        config = MercadoPagoConfig.get_config()
        if not config.access_token:
            return Response(
                {'detail': 'Access Token não configurado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        client = MercadoPagoClient()
        
        # Testar com busca de métodos de pagamento
        result = client._make_request('GET', 'v1/payment_methods')
        
        return Response({
            'message': 'Conexão testada com sucesso',
            'environment': config.environment_name,
            'payment_methods_count': len(result),
            'api_status': 'Conectado'
        })
        
    except Exception as e:
        return Response(
            {'detail': f'Erro na conexão: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

@csrf_exempt
@api_view(['POST'])
@permission_classes([])
def mercadopago_webhook(request):
    """Webhook do Mercado Pago"""
    try:
        logger.info(f"Webhook Mercado Pago recebido: {request.data}")
        
        # Mercado Pago envia notificações diferentes
        notification_type = request.data.get('type')
        
        if notification_type == 'payment':
            payment_id = request.data.get('data', {}).get('id')
            
            if payment_id:
                # Buscar pagamento atualizado
                client = MercadoPagoClient()
                payment_data = client.get_payment(payment_id)
                
                # Atualizar pagamento local
                try:
                    payment = MercadoPagoPayment.objects.get(mp_id=payment_id)
                    
                    old_status = payment.status
                    payment.status = payment_data['status']
                    payment.status_detail = payment_data.get('status_detail', '')
                    
                    if payment_data.get('date_approved'):
                        payment.date_approved = datetime.fromisoformat(
                            payment_data['date_approved'].replace('Z', '+00:00')
                        )
                    
                    payment.raw_data = payment_data
                    payment.save()
                    
                    logger.info(f"Pagamento MP {payment_id} atualizado: {old_status} -> {payment.status}")
                    
                    # Se foi aprovado, atualizar financeiro da loja
                    if payment.status == 'approved' and old_status != 'approved':
                        self._update_loja_financeiro(payment)
                    
                except MercadoPagoPayment.DoesNotExist:
                    logger.warning(f"Pagamento MP {payment_id} não encontrado localmente")
        
        return Response({'status': 'processed'}, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erro no webhook Mercado Pago: {e}")
        return Response({'status': 'error'}, status=status.HTTP_200_OK)

def _update_loja_financeiro(payment):
    """Atualizar financeiro da loja após pagamento aprovado"""
    try:
        # Buscar loja pela external_reference
        external_ref = payment.external_reference
        if 'loja_' in external_ref:
            loja_slug = external_ref.replace('loja_', '').replace('_assinatura', '').replace('_pix', '')
            
            from superadmin.models import Loja
            loja = Loja.objects.get(slug=loja_slug, is_active=True)
            
            # Atualizar financeiro
            financeiro = loja.financeiro
            financeiro.status_pagamento = 'ativo'
            financeiro.ultimo_pagamento = timezone.now()
            financeiro.save()
            
            # Desbloquear loja se estiver bloqueada
            if loja.is_blocked:
                loja.is_blocked = False
                loja.blocked_at = None
                loja.blocked_reason = ''
                loja.save()
            
            logger.info(f"Financeiro da loja {loja_slug} atualizado via webhook MP")
            
    except Exception as e:
        logger.error(f"Erro ao atualizar financeiro via webhook MP: {e}")

class MercadoPagoPaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para pagamentos Mercado Pago"""
    serializer_class = MercadoPagoPaymentSerializer
    permission_classes = [IsSuperAdmin]
    queryset = MercadoPagoPayment.objects.all().select_related('customer')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-date_created')
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Atualizar status consultando Mercado Pago"""
        try:
            payment = self.get_object()
            
            client = MercadoPagoClient()
            result = client.get_payment(payment.mp_id)
            
            old_status = payment.status
            payment.status = result['status']
            payment.status_detail = result.get('status_detail', '')
            payment.raw_data = result
            payment.save()
            
            return Response({
                'success': True,
                'old_status': old_status,
                'new_status': payment.status,
                'message': 'Status atualizado com sucesso'
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

## Conclusão

Este exemplo mostra como seria a implementação completa do módulo Mercado Pago, seguindo a mesma estrutura do módulo Asaas existente. A implementação inclui:

1. **Modelos completos** para clientes, pagamentos e assinaturas
2. **Cliente da API** com todos os métodos necessários
3. **Serviços de pagamento** para boleto e PIX
4. **Views da API** para configuração e monitoramento
5. **Webhook** para sincronização automática
6. **Integração** com o sistema de financeiro existente

A próxima etapa seria implementar o serviço unificado que permite usar ambos os provedores (Asaas e Mercado Pago) de forma transparente.