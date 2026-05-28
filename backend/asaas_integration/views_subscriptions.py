"""
ViewSet para assinaturas Asaas
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
import logging

from core.throttling import DashboardRateThrottle

from .models import AsaasPayment, LojaAssinatura
from .serializers import LojaAssinaturaSerializer
from .views_config import IsSuperAdmin, REQUESTS_AVAILABLE
from superadmin.models import Loja

# Importação condicional do cliente Asaas
if REQUESTS_AVAILABLE:
    try:
        from .client import AsaasClient
    except ImportError:
        AsaasClient = None
else:
    AsaasClient = None

logger = logging.getLogger(__name__)


class AsaasSubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para assinaturas Asaas (somente leitura para superadmin)"""
    serializer_class = LojaAssinaturaSerializer
    permission_classes = [IsSuperAdmin]
    queryset = LojaAssinatura.objects.all().select_related('asaas_customer', 'current_payment')
    
    def get_queryset(self):
        """Filtrar assinaturas com ordenação"""
        queryset = super().get_queryset()
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'], throttle_classes=[DashboardRateThrottle])
    def dashboard_stats(self, request):
        """
        Estatísticas para dashboard financeiro.
        Rate limited: 10 requisições por minuto para prevenir loops infinitos.
        """
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
    
    def _get_dia_vencimento(self, loja):
        """Buscar dia de vencimento configurado da loja"""
        try:
            return loja.financeiro.dia_vencimento
        except AttributeError:
            logger.warning(f"Financeiro não encontrado para loja {loja.nome}, usando dia padrão 10")
            return 10
    
    def _calcular_proxima_data_vencimento(self, dia_vencimento):
        """Calcular próxima data de vencimento baseada no dia configurado"""
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        
        hoje = datetime.now().date()
        proxima_data = hoje + relativedelta(months=1)
        
        try:
            proxima_data = proxima_data.replace(day=dia_vencimento)
        except ValueError:
            # Dia não existe no mês (ex: 31 em fevereiro), usar último dia do mês
            proxima_data = (proxima_data.replace(day=1) + relativedelta(months=1) - relativedelta(days=1))
        
        return proxima_data
    
    def _preparar_dados_loja(self, loja):
        """Preparar dados da loja para criação de cobrança"""
        return {
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
    
    def _preparar_dados_plano(self, assinatura):
        """Preparar dados do plano para criação de cobrança"""
        return {
            'nome': assinatura.plano_nome,
            'preco': float(assinatura.plano_valor)
        }
    
    @action(detail=True, methods=['post'])
    def generate_new_payment(self, request, pk=None):
        """Gerar nova cobrança para assinatura"""
        try:
            # Validar disponibilidade do serviço Asaas
            if not AsaasClient:
                return Response(
                    {'error': 'Serviço Asaas não disponível'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Buscar assinatura e loja
            assinatura = self.get_object()
            loja = Loja.objects.select_related('owner', 'financeiro').get(slug=assinatura.loja_slug)
            
            # Calcular data de vencimento
            dia_vencimento = self._get_dia_vencimento(loja)
            proxima_data = self._calcular_proxima_data_vencimento(dia_vencimento)
            due_date_str = proxima_data.strftime('%Y-%m-%d')
            
            # Log informativo
            logger.info(f"📅 Gerando nova cobrança para {loja.nome}")
            logger.info(f"   - Dia de vencimento: {dia_vencimento}")
            logger.info(f"   - Próxima data: {due_date_str}")
            
            # Preparar dados
            loja_data = self._preparar_dados_loja(loja)
            plano_data = self._preparar_dados_plano(assinatura)
            
            # Criar cobrança
            from .client import AsaasPaymentService
            service = AsaasPaymentService()
            
            # Usar customer_id existente da assinatura
            customer_id = assinatura.asaas_customer.asaas_id if assinatura.asaas_customer else None
            
            resultado = service.create_loja_subscription_payment(
                loja_data, 
                plano_data, 
                due_date=due_date_str,
                customer_id=customer_id
            )
            
            # Retornar resultado
            if resultado.get('success'):
                return Response({
                    'success': True,
                    'message': 'Nova cobrança gerada com sucesso',
                    'payment_id': resultado.get('payment_id'),
                    'due_date': due_date_str
                })
            
            return Response(
                {'error': resultado.get('error', 'Erro ao gerar cobrança')},
                status=status.HTTP_400_BAD_REQUEST
            )
                
        except Loja.DoesNotExist:
            logger.error(f"Loja não encontrada: {assinatura.loja_slug}")
            return Response(
                {'error': 'Loja não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erro ao gerar nova cobrança: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'error': f'Erro interno: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    
    @action(detail=True, methods=['post'])
    def create_manual_payment(self, request, pk=None):
        """Criar cobrança manual com data personalizada"""
        try:
            # Validar disponibilidade do serviço Asaas
            if not AsaasClient:
                return Response(
                    {'error': 'Serviço Asaas não disponível'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Buscar assinatura e loja
            assinatura = self.get_object()
            loja = Loja.objects.select_related('owner', 'financeiro').get(slug=assinatura.loja_slug)
            
            # Obter data de vencimento do request
            due_date_str = request.data.get('due_date')
            if not due_date_str:
                return Response(
                    {'error': 'Data de vencimento é obrigatória'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validar formato da data
            from datetime import datetime
            try:
                datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                return Response(
                    {'error': 'Formato de data inválido. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Log informativo
            logger.info(f"📅 Criando cobrança manual para {loja.nome}")
            logger.info(f"   - Data de vencimento: {due_date_str}")
            
            # Preparar dados
            loja_data = self._preparar_dados_loja(loja)
            plano_data = self._preparar_dados_plano(assinatura)
            
            # Buscar customer_id existente da assinatura
            customer_id = assinatura.asaas_customer.asaas_id if assinatura.asaas_customer else None
            logger.info(f"📝 Customer ID da assinatura: {customer_id}")
            
            # Criar cobrança usando o customer existente
            from .client import AsaasPaymentService
            service = AsaasPaymentService()
            resultado = service.create_loja_subscription_payment(
                loja_data, 
                plano_data, 
                due_date=due_date_str,
                customer_id=customer_id  # Usar customer existente
            )
            
            # Salvar no banco de dados local
            if resultado.get('success'):
                from .models import AsaasPayment, AsaasCustomer, LojaAssinatura
                from superadmin.models import FinanceiroLoja, PagamentoLoja
                
                # Buscar customer existente da assinatura (não criar novo)
                try:
                    loja_assinatura = LojaAssinatura.objects.get(loja_slug=loja.slug)
                    customer = loja_assinatura.asaas_customer
                    logger.info(f"✅ Usando customer existente da assinatura: {customer.asaas_id}")
                except LojaAssinatura.DoesNotExist:
                    # Fallback: criar ou buscar customer se não houver assinatura
                    logger.warning(f"⚠️ LojaAssinatura não encontrada, criando/buscando customer")
                    customer, _ = AsaasCustomer.objects.get_or_create(
                        asaas_id=resultado['customer_id'],
                        defaults={
                            'name': loja.nome,
                            'email': loja.owner.email,
                            'cpf_cnpj': loja_data.get('cpf_cnpj', ''),
                            'phone': loja_data.get('telefone', ''),
                        }
                    )
                
                # Criar pagamento no AsaasPayment
                payment = AsaasPayment.objects.create(
                    customer=customer,
                    asaas_id=resultado['payment_id'],
                    value=resultado['value'],
                    status=resultado['status'],
                    due_date=resultado['due_date'],
                    description=f"Assinatura {plano_data['nome']} - Loja {loja.nome}",
                    bank_slip_url=resultado.get('boleto_url', ''),
                    pix_copy_paste=resultado.get('pix_copy_paste', ''),
                    external_reference=f"loja_{loja.slug}_assinatura"
                )
                
                logger.info(f"✅ Pagamento salvo no AsaasPayment (ID: {payment.id})")
                
                # Criar pagamento no PagamentoLoja (para histórico da loja)
                try:
                    financeiro = FinanceiroLoja.objects.get(loja=loja)
                    
                    # Calcular referência do mês baseado na data de vencimento
                    from datetime import datetime
                    due_date_obj = datetime.strptime(resultado['due_date'], '%Y-%m-%d').date()
                    referencia_mes = due_date_obj.replace(day=1)
                    
                    pagamento_loja = PagamentoLoja.objects.create(
                        loja=loja,
                        financeiro=financeiro,
                        asaas_payment_id=resultado['payment_id'],
                        valor=resultado['value'],
                        status='pendente',
                        data_vencimento=resultado['due_date'],
                        referencia_mes=referencia_mes,
                        forma_pagamento='boleto',
                        boleto_url=resultado.get('boleto_url', ''),
                        boleto_pdf_url=resultado.get('boleto_url', ''),
                        pix_copy_paste=resultado.get('pix_copy_paste', '')
                    )
                    
                    logger.info(f"✅ Pagamento salvo no PagamentoLoja (ID: {pagamento_loja.id})")
                except FinanceiroLoja.DoesNotExist:
                    logger.error(f"❌ FinanceiroLoja não encontrado para {loja.slug}, não foi possível criar PagamentoLoja")
                except Exception as e:
                    logger.error(f"❌ Erro ao criar PagamentoLoja: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                # Atualizar current_payment da assinatura
                assinatura.current_payment = payment
                assinatura.save()
                logger.info(f"✅ Assinatura atualizada com novo pagamento atual")
                
                # Atualizar FinanceiroLoja com dados do novo boleto
                try:
                    financeiro = FinanceiroLoja.objects.get(loja=loja)
                    financeiro.asaas_customer_id = resultado['customer_id']
                    financeiro.asaas_payment_id = resultado['payment_id']
                    financeiro.boleto_url = resultado.get('boleto_url', '')
                    financeiro.pix_qr_code = resultado.get('pix_qr_code', '')
                    # ✅ CORREÇÃO: Para plano anual, próxima cobrança = +1 ano (não a data do boleto atual)
                    from superadmin.cobranca_service import CobrancaService
                    dia = financeiro.dia_vencimento or 10
                    financeiro.data_proxima_cobranca = CobrancaService()._calcular_proxima_cobranca(dia, loja.tipo_assinatura)
                    financeiro.save()
                    logger.info(f"✅ FinanceiroLoja atualizado (próxima cobrança: {financeiro.data_proxima_cobranca})")
                except FinanceiroLoja.DoesNotExist:
                    logger.warning(f"⚠️  FinanceiroLoja não encontrado para {loja.slug}")
                
                return Response({
                    'success': True,
                    'message': 'Cobrança manual criada com sucesso',
                    'payment_id': resultado.get('payment_id'),
                    'due_date': due_date_str,
                    'local_payment_id': payment.id
                })
            
            return Response(
                {'error': resultado.get('error', 'Erro ao criar cobrança')},
                status=status.HTTP_400_BAD_REQUEST
            )
                
        except Loja.DoesNotExist:
            logger.error(f"Loja não encontrada: {assinatura.loja_slug}")
            return Response(
                {'error': 'Loja não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erro ao criar cobrança manual: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'error': f'Erro interno: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
