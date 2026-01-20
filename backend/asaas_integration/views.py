"""
Views para integração com Asaas
Gerencia cobranças e pagamentos no painel financeiro
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db import transaction
from datetime import datetime, timedelta
import logging

from .models import AsaasCustomer, AsaasPayment, LojaAssinatura
from .serializers import AsaasCustomerSerializer, AsaasPaymentSerializer, LojaAssinaturaSerializer
from .client import AsaasPaymentService

logger = logging.getLogger(__name__)

class AsaasCustomerViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para clientes Asaas"""
    queryset = AsaasCustomer.objects.all()
    serializer_class = AsaasCustomerSerializer
    permission_classes = [IsAuthenticated]

class AsaasPaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para cobranças Asaas"""
    queryset = AsaasPayment.objects.all()
    serializer_class = AsaasPaymentSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """Baixa PDF do boleto"""
        payment = self.get_object()
        
        try:
            service = AsaasPaymentService()
            pdf_content = service.download_boleto_pdf(payment.asaas_id)
            
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="boleto_{payment.asaas_id}.pdf"'
            return response
            
        except Exception as e:
            logger.error(f"Erro ao baixar PDF: {e}")
            return Response(
                {'error': 'Erro ao baixar PDF do boleto'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Atualiza status do pagamento consultando a API"""
        payment = self.get_object()
        
        try:
            service = AsaasPaymentService()
            result = service.get_payment_status(payment.asaas_id)
            
            if result['success']:
                payment.status = result['status']
                if result.get('payment_date'):
                    payment.payment_date = datetime.fromisoformat(result['payment_date'].replace('Z', '+00:00'))
                payment.raw_data = result['raw_payment']
                payment.save()
                
                return Response({
                    'success': True,
                    'status': payment.status,
                    'payment_date': payment.payment_date
                })
            else:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Erro ao atualizar status: {e}")
            return Response(
                {'error': 'Erro ao consultar status do pagamento'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class LojaAssinaturaViewSet(viewsets.ModelViewSet):
    """ViewSet para assinaturas das lojas"""
    queryset = LojaAssinatura.objects.all()
    serializer_class = LojaAssinaturaSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def create_for_loja(self, request):
        """Cria assinatura para uma nova loja"""
        try:
            loja_data = request.data.get('loja', {})
            plano_data = request.data.get('plano', {})
            
            if not loja_data or not plano_data:
                return Response(
                    {'error': 'Dados da loja e plano são obrigatórios'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar se já existe assinatura para esta loja
            if LojaAssinatura.objects.filter(loja_slug=loja_data['slug']).exists():
                return Response(
                    {'error': 'Já existe uma assinatura para esta loja'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            with transaction.atomic():
                # Criar cobrança no Asaas
                service = AsaasPaymentService()
                result = service.create_loja_subscription_payment(loja_data, plano_data)
                
                if not result['success']:
                    return Response(
                        {'error': result['error']},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Criar cliente no banco local
                customer = AsaasCustomer.objects.create(
                    asaas_id=result['customer_id'],
                    name=loja_data['nome'],
                    email=loja_data['email'],
                    cpf_cnpj=loja_data['cpf_cnpj'],
                    phone=loja_data.get('telefone', ''),
                    address=loja_data.get('endereco', ''),
                    address_number=loja_data.get('numero', ''),
                    complement=loja_data.get('complemento', ''),
                    province=loja_data.get('bairro', ''),
                    city=loja_data.get('cidade', ''),
                    state=loja_data.get('estado', ''),
                    postal_code=loja_data.get('cep', ''),
                    external_reference=f"loja_{loja_data['slug']}",
                    raw_data=result['raw_customer']
                )
                
                # Criar pagamento no banco local
                payment = AsaasPayment.objects.create(
                    asaas_id=result['payment_id'],
                    customer=customer,
                    external_reference=f"loja_{loja_data['slug']}_assinatura",
                    billing_type='BOLETO',
                    status=result['status'],
                    value=result['value'],
                    due_date=datetime.strptime(result['due_date'], '%Y-%m-%d').date(),
                    invoice_url=result['payment_url'],
                    bank_slip_url=result['boleto_url'],
                    pix_qr_code=result['pix_qr_code'],
                    pix_copy_paste=result['pix_copy_paste'],
                    description=f"Assinatura {plano_data['nome']} - Loja {loja_data['nome']}",
                    raw_data=result['raw_payment']
                )
                
                # Criar assinatura
                assinatura = LojaAssinatura.objects.create(
                    loja_slug=loja_data['slug'],
                    loja_nome=loja_data['nome'],
                    asaas_customer=customer,
                    current_payment=payment,
                    plano_nome=plano_data['nome'],
                    plano_valor=plano_data['preco'],
                    data_vencimento=payment.due_date
                )
                
                return Response({
                    'success': True,
                    'assinatura_id': assinatura.id,
                    'payment_id': payment.asaas_id,
                    'payment_url': payment.invoice_url,
                    'boleto_url': payment.bank_slip_url,
                    'pix_qr_code': payment.pix_qr_code,
                    'pix_copy_paste': payment.pix_copy_paste,
                    'due_date': payment.due_date,
                    'value': float(payment.value)
                })
                
        except Exception as e:
            logger.error(f"Erro ao criar assinatura: {e}")
            return Response(
                {'error': f'Erro interno: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def generate_new_payment(self, request, pk=None):
        """Gera nova cobrança para renovação da assinatura"""
        assinatura = self.get_object()
        
        try:
            with transaction.atomic():
                # Dados para nova cobrança
                loja_data = {
                    'nome': assinatura.loja_nome,
                    'slug': assinatura.loja_slug,
                    'email': assinatura.asaas_customer.email,
                    'cpf_cnpj': assinatura.asaas_customer.cpf_cnpj,
                    'telefone': assinatura.asaas_customer.phone,
                }
                
                plano_data = {
                    'nome': assinatura.plano_nome,
                    'preco': assinatura.plano_valor
                }
                
                # Criar nova cobrança
                service = AsaasPaymentService()
                result = service.create_loja_subscription_payment(loja_data, plano_data)
                
                if not result['success']:
                    return Response(
                        {'error': result['error']},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Criar novo pagamento no banco local
                payment = AsaasPayment.objects.create(
                    asaas_id=result['payment_id'],
                    customer=assinatura.asaas_customer,
                    external_reference=f"loja_{assinatura.loja_slug}_renovacao",
                    billing_type='BOLETO',
                    status=result['status'],
                    value=result['value'],
                    due_date=datetime.strptime(result['due_date'], '%Y-%m-%d').date(),
                    invoice_url=result['payment_url'],
                    bank_slip_url=result['boleto_url'],
                    pix_qr_code=result['pix_qr_code'],
                    pix_copy_paste=result['pix_copy_paste'],
                    description=f"Renovação {assinatura.plano_nome} - Loja {assinatura.loja_nome}",
                    raw_data=result['raw_payment']
                )
                
                # Atualizar assinatura
                assinatura.current_payment = payment
                assinatura.data_vencimento = payment.due_date
                assinatura.save()
                
                return Response({
                    'success': True,
                    'payment_id': payment.asaas_id,
                    'payment_url': payment.invoice_url,
                    'boleto_url': payment.bank_slip_url,
                    'pix_qr_code': payment.pix_qr_code,
                    'pix_copy_paste': payment.pix_copy_paste,
                    'due_date': payment.due_date,
                    'value': float(payment.value)
                })
                
        except Exception as e:
            logger.error(f"Erro ao gerar nova cobrança: {e}")
            return Response(
                {'error': f'Erro interno: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Estatísticas para o dashboard financeiro"""
        try:
            total_assinaturas = LojaAssinatura.objects.count()
            assinaturas_ativas = LojaAssinatura.objects.filter(ativa=True).count()
            
            # Pagamentos por status
            pagamentos_pendentes = AsaasPayment.objects.filter(status='PENDING').count()
            pagamentos_pagos = AsaasPayment.objects.filter(status__in=['RECEIVED', 'CONFIRMED']).count()
            pagamentos_vencidos = AsaasPayment.objects.filter(status='OVERDUE').count()
            
            # Receita total
            from django.db.models import Sum
            receita_total = AsaasPayment.objects.filter(
                status__in=['RECEIVED', 'CONFIRMED']
            ).aggregate(total=Sum('value'))['total'] or 0
            
            receita_pendente = AsaasPayment.objects.filter(
                status='PENDING'
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
            logger.error(f"Erro ao buscar estatísticas: {e}")
            return Response(
                {'error': 'Erro ao buscar estatísticas'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )