"""
Serviço unificado para criação de cobranças (Asaas + Mercado Pago)

Usa Strategy Pattern para abstrair a lógica de cada provedor de pagamento,
facilitando manutenção e adição de novos provedores.

Baseado no payment_deletion_service.py existente.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import date, timedelta
from calendar import monthrange

logger = logging.getLogger(__name__)


class PaymentProviderStrategy(ABC):
    """Interface abstrata para estratégias de provedor de pagamento"""
    
    @abstractmethod
    def criar_cobranca(self, loja, financeiro) -> Dict[str, Any]:
        """
        Cria cobrança no provedor de pagamento
        
        Args:
            loja: Instância do modelo Loja
            financeiro: Instância do modelo FinanceiroLoja
        
        Returns:
            dict com success, payment_id, boleto_url, pix_qr_code, pix_copy_paste, error
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Retorna nome do provedor"""
        pass


class AsaasPaymentStrategy(PaymentProviderStrategy):
    """Estratégia para criação de cobranças no Asaas"""
    
    def get_provider_name(self) -> str:
        return 'asaas'
    
    def criar_cobranca(self, loja, financeiro) -> Dict[str, Any]:
        """Cria cobrança no Asaas"""
        try:
            from asaas_integration.client import AsaasPaymentService
            from asaas_integration.models import AsaasCustomer, AsaasPayment, LojaAssinatura
            from django.db import transaction
            from datetime import datetime
            
            logger.info(f"Criando cobrança Asaas para loja: {loja.nome}")
            
            # Preparar dados
            due_date_str = financeiro.data_proxima_cobranca.strftime('%Y-%m-%d')
            
            loja_data = {
                'nome': loja.nome,
                'slug': loja.slug,
                'email': loja.owner.email,
                'cpf_cnpj': loja.cpf_cnpj or '000.000.000-00',
                'telefone': getattr(loja.owner, 'telefone', ''),
                # ✅ CORREÇÃO v1320: Incluir endereço completo para emissão de NF
                'endereco': loja.logradouro or '',
                'numero': loja.numero or '',
                'complemento': loja.complemento or '',
                'bairro': loja.bairro or '',
                'cidade': loja.cidade or '',
                'estado': loja.uf or '',
                'cep': loja.cep or '',
            }
            
            valor_plano = loja.plano.preco_anual if loja.tipo_assinatura == 'anual' else loja.plano.preco_mensal
            plano_data = {
                'nome': f"{loja.plano.nome} ({loja.get_tipo_assinatura_display()})",
                'preco': valor_plano
            }
            
            # Criar cobrança no Asaas
            service = AsaasPaymentService()
            
            # Verificar se já existe customer_id no financeiro
            customer_id = financeiro.asaas_customer_id if financeiro.asaas_customer_id else None
            
            result = service.create_loja_subscription_payment(
                loja_data, 
                plano_data, 
                due_date=due_date_str,
                customer_id=customer_id
            )
            
            if not result['success']:
                logger.error(f"Erro ao criar cobrança Asaas: {result['error']}")
                return result
            
            # Salvar no banco local
            with transaction.atomic():
                # Criar/atualizar cliente
                customer, _ = AsaasCustomer.objects.update_or_create(
                    asaas_id=result['customer_id'],
                    defaults={
                        'name': loja_data['nome'],
                        'email': loja_data['email'],
                        'cpf_cnpj': loja_data['cpf_cnpj'],
                        'phone': loja_data.get('telefone', ''),
                        'external_reference': f"loja_{loja_data['slug']}",
                        'raw_data': result.get('raw_customer', {})
                    }
                )
                
                # Criar pagamento
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
                    pix_qr_code=result.get('pix_qr_code', ''),
                    pix_copy_paste=result.get('pix_copy_paste', ''),
                    description=f"Assinatura {plano_data['nome']} - Loja {loja_data['nome']}",
                    raw_data=result.get('raw_payment', {})
                )
                
                # Criar/atualizar assinatura
                LojaAssinatura.objects.update_or_create(
                    loja_slug=loja_data['slug'],
                    defaults={
                        'loja_nome': loja_data['nome'],
                        'asaas_customer': customer,
                        'current_payment': payment,
                        'plano_nome': plano_data['nome'],
                        'plano_valor': plano_data['preco'],
                        'data_vencimento': payment.due_date
                    }
                )
                
                # Atualizar FinanceiroLoja
                financeiro.provedor_boleto = 'asaas'
                financeiro.asaas_customer_id = result['customer_id']
                financeiro.asaas_payment_id = result['payment_id']
                financeiro.boleto_url = result.get('boleto_url', '')
                financeiro.pix_qr_code = result.get('pix_qr_code', '')
                financeiro.pix_copy_paste = result.get('pix_copy_paste', '')
                financeiro.save(update_fields=[
                    'provedor_boleto', 'asaas_customer_id', 'asaas_payment_id',
                    'boleto_url', 'pix_qr_code', 'pix_copy_paste'
                ])
            
            logger.info(f"✅ Cobrança Asaas criada: payment_id={result['payment_id']}")
            
            return {
                'success': True,
                'provedor': 'asaas',
                'payment_id': result['payment_id'],
                'boleto_url': result.get('boleto_url', ''),
                'pix_qr_code': result.get('pix_qr_code', ''),
                'pix_copy_paste': result.get('pix_copy_paste', ''),
                'due_date': result['due_date'],
                'value': result['value']
            }
            
        except Exception as e:
            logger.exception(f"Erro ao criar cobrança Asaas para loja {loja.slug}: {e}")
            return {'success': False, 'error': str(e)}


class MercadoPagoPaymentStrategy(PaymentProviderStrategy):
    """Estratégia para criação de cobranças no Mercado Pago"""
    
    def get_provider_name(self) -> str:
        return 'mercadopago'
    
    def criar_cobranca(self, loja, financeiro) -> Dict[str, Any]:
        """Cria cobrança no Mercado Pago"""
        try:
            from superadmin.mercadopago_service import LojaMercadoPagoService
            
            logger.info(f"Criando cobrança Mercado Pago para loja: {loja.nome}")
            
            # Usar serviço existente
            service = LojaMercadoPagoService()
            result = service.criar_cobranca_loja(loja, financeiro, criar_pix=True)
            
            if not result.get('success'):
                logger.error(f"Erro ao criar cobrança Mercado Pago: {result.get('error')}")
                return result
            
            # Atualizar FinanceiroLoja
            financeiro.provedor_boleto = 'mercadopago'
            financeiro.mercadopago_payment_id = result.get('payment_id', '')[:100]
            financeiro.mercadopago_pix_payment_id = result.get('pix_payment_id', '')[:100]
            financeiro.boleto_url = result.get('boleto_url', '')[:200]
            financeiro.pix_qr_code = result.get('pix_qr_code', '')[:2000]
            financeiro.pix_copy_paste = result.get('pix_copy_paste', '')[:500]
            financeiro.save(update_fields=[
                'provedor_boleto', 'mercadopago_payment_id', 'mercadopago_pix_payment_id',
                'boleto_url', 'pix_qr_code', 'pix_copy_paste'
            ])
            
            logger.info(f"✅ Cobrança Mercado Pago criada: payment_id={result.get('payment_id')}")
            
            return {
                'success': True,
                'provedor': 'mercadopago',
                'payment_id': result.get('payment_id'),
                'boleto_url': result.get('boleto_url', ''),
                'pix_qr_code': result.get('pix_qr_code', ''),
                'pix_copy_paste': result.get('pix_copy_paste', ''),
                'due_date': result.get('due_date'),
                'value': result.get('value')
            }
            
        except Exception as e:
            logger.exception(f"Erro ao criar cobrança Mercado Pago para loja {loja.slug}: {e}")
            return {'success': False, 'error': str(e)}


class CobrancaService:
    """
    Serviço unificado para criação de cobranças
    
    Usa Strategy Pattern para abstrair a lógica de cada provedor.
    """
    
    def __init__(self):
        self.strategies = {
            'asaas': AsaasPaymentStrategy(),
            'mercadopago': MercadoPagoPaymentStrategy()
        }
    
    def criar_cobranca(self, loja, financeiro) -> Dict[str, Any]:
        """
        Cria cobrança no provedor escolhido pela loja
        
        Args:
            loja: Instância do modelo Loja
            financeiro: Instância do modelo FinanceiroLoja
        
        Returns:
            dict com success, provedor, payment_id, boleto_url, pix_qr_code, error
        """
        # Validar dados da loja
        validation_error = self._validar_dados_loja(loja)
        if validation_error:
            return {'success': False, 'error': validation_error}
        
        # Escolher provedor
        provedor = loja.provedor_boleto_preferido or 'asaas'
        strategy = self.strategies.get(provedor)
        
        if not strategy:
            return {'success': False, 'error': f'Provedor {provedor} não suportado'}
        
        logger.info(f"Criando cobrança para loja {loja.slug} usando provedor {provedor}")
        
        # Criar cobrança
        return strategy.criar_cobranca(loja, financeiro)
    
    def renovar_cobranca(self, loja, financeiro, dia_vencimento=None) -> Dict[str, Any]:
        """
        Cria nova cobrança para renovação de assinatura
        
        Args:
            loja: Instância do modelo Loja
            financeiro: Instância do modelo FinanceiroLoja
            dia_vencimento: Dia do mês para vencimento (opcional)
        
        Returns:
            dict com success, provedor, payment_id, boleto_url, pix_qr_code, error
        """
        # Atualizar data_proxima_cobranca se dia_vencimento fornecido
        if dia_vencimento:
            financeiro.dia_vencimento = dia_vencimento
            financeiro.data_proxima_cobranca = self._calcular_proxima_cobranca(dia_vencimento)
            financeiro.save(update_fields=['dia_vencimento', 'data_proxima_cobranca'])
            logger.info(f"Data de vencimento atualizada para dia {dia_vencimento}")
        
        # Criar cobrança usando mesmo fluxo
        return self.criar_cobranca(loja, financeiro)
    
    def _validar_dados_loja(self, loja) -> str:
        """
        Valida dados necessários para criar cobrança
        
        Returns:
            str com mensagem de erro ou None se válido
        """
        if not loja.cpf_cnpj:
            return 'CPF/CNPJ da loja é obrigatório'
        
        if not loja.owner or not loja.owner.email:
            return 'Email do administrador da loja é obrigatório'
        
        # Validações específicas do Mercado Pago
        if loja.provedor_boleto_preferido == 'mercadopago':
            campos_obrigatorios = {
                'cep': 'CEP',
                'logradouro': 'Logradouro',
                'cidade': 'Cidade',
                'uf': 'UF'
            }
            
            for campo, nome in campos_obrigatorios.items():
                if not getattr(loja, campo, None):
                    return f'{nome} é obrigatório para boletos do Mercado Pago'
        
        return None
    
    def _calcular_proxima_cobranca(self, dia_vencimento: int) -> date:
        """
        Calcula próxima data de cobrança baseada no dia de vencimento
        
        Args:
            dia_vencimento: Dia do mês (1-28)
        
        Returns:
            date da próxima cobrança (sempre no próximo mês)
        """
        hoje = date.today()
        
        # Calcular próximo mês
        if hoje.month == 12:
            proximo_mes = 1
            proximo_ano = hoje.year + 1
        else:
            proximo_mes = hoje.month + 1
            proximo_ano = hoje.year
        
        # Ajustar dia se o mês não tiver esse dia (ex: dia 31 em fevereiro)
        ultimo_dia_mes = monthrange(proximo_ano, proximo_mes)[1]
        dia_cobranca = min(dia_vencimento, ultimo_dia_mes)
        
        return date(proximo_ano, proximo_mes, dia_cobranca)
