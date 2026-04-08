"""
Serviço para integração com Asaas na criação de lojas
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)

class LojaAsaasService:
    """Serviço para criar cobrança Asaas quando uma loja é criada"""
    
    def __init__(self):
        # Importação condicional para evitar erro se asaas_integration não estiver disponível
        try:
            from asaas_integration.models import AsaasConfig
            from asaas_integration.client import AsaasPaymentService
            self.AsaasConfig = AsaasConfig
            self.AsaasPaymentService = AsaasPaymentService
            self.available = True
        except ImportError:
            logger.warning("Asaas integration não disponível")
            self.available = False
    
    def criar_cobranca_loja(self, loja, financeiro):
        """
        Cria cobrança (boleto) para a loja. Usa Mercado Pago se configurado e
        use_for_boletos ativo; caso contrário usa Asaas.
        
        Args:
            loja: Instância da Loja
            financeiro: Instância do FinanceiroLoja
            
        Returns:
            dict: Resultado da criação da cobrança
        """
        # Opção: Mercado Pago para boletos (preferência da loja ou global)
        try:
            from .models import MercadoPagoConfig
            from .mercadopago_service import LojaMercadoPagoService
            mp_config = MercadoPagoConfig.get_config()
            usar_mp = (
                mp_config.enabled
                and mp_config.access_token
                and getattr(loja, 'provedor_boleto_preferido', 'asaas') == 'mercadopago'
            )
            if usar_mp:
                mp_service = LojaMercadoPagoService()
                if mp_service.available:
                    resultado = mp_service.criar_cobranca_loja(loja, financeiro)
                    if resultado.get('success'):
                        # Limitar boleto_url a 200 chars (URLField default) para evitar "value too long"
                        boleto_url = (resultado.get('boleto_url') or '')[:200]
                        pix_qr = (resultado.get('pix_qr_code') or '')[:2000]
                        pix_paste = (resultado.get('pix_copy_paste') or '')[:500]
                        pix_pid = (resultado.get('pix_payment_id') or '')[:100]
                        financeiro.provedor_boleto = 'mercadopago'
                        financeiro.mercadopago_payment_id = (resultado.get('payment_id') or '')[:100]
                        financeiro.mercadopago_pix_payment_id = pix_pid
                        financeiro.asaas_customer_id = ''
                        financeiro.asaas_payment_id = ''
                        financeiro.boleto_url = boleto_url
                        financeiro.pix_qr_code = pix_qr
                        financeiro.pix_copy_paste = pix_paste
                        financeiro.status_pagamento = 'pendente'
                        financeiro.save()
                        from .models import PagamentoLoja
                        pagamento = PagamentoLoja.objects.create(
                            loja=loja,
                            financeiro=financeiro,
                            valor=financeiro.valor_mensalidade,
                            referencia_mes=financeiro.data_proxima_cobranca.replace(day=1),
                            status='pendente',
                            forma_pagamento='boleto',
                            data_vencimento=financeiro.data_proxima_cobranca,
                            provedor_boleto='mercadopago',
                            mercadopago_payment_id=(resultado.get('payment_id') or '')[:100],
                            mercadopago_pix_payment_id=pix_pid,
                            asaas_payment_id='',
                            boleto_url=boleto_url,
                            pix_qr_code=pix_qr,
                            pix_copy_paste=pix_paste,
                        )
                        logger.info(f"Cobrança Mercado Pago criada para loja {loja.nome}: {resultado.get('payment_id')}" + (f", PIX: {pix_pid}" if pix_pid else ""))
                        return {
                            'success': True,
                            'provedor': 'mercadopago',
                            'payment_id': resultado.get('payment_id'),
                            'customer_id': '',
                            'boleto_url': resultado.get('boleto_url'),
                            'pix_qr_code': pix_qr or resultado.get('pix_qr_code'),
                            'pix_copy_paste': pix_paste or resultado.get('pix_copy_paste'),
                            'due_date': resultado.get('due_date'),
                            'value': resultado.get('value'),
                            'pagamento_id': pagamento.id,
                        }
                    return resultado
        except Exception as e:
            logger.warning("Mercado Pago não usado para cobrança: %s", e)
        # Fallback: Asaas
        if not self.available:
            return {
                'success': False,
                'error': 'Integração Asaas não disponível'
            }
        
        try:
            # Verificar se Asaas está configurado
            config = self.AsaasConfig.get_config()
            if not config.api_key or not config.enabled:
                logger.warning("Asaas não configurado ou desabilitado")
                return {
                    'success': False,
                    'error': 'Asaas não configurado'
                }
            
            # Preparar dados da loja
            loja_data = {
                'nome': loja.nome,
                'email': loja.owner.email,
                'cpf_cnpj': loja.cpf_cnpj or '00000000000',  # CPF/CNPJ obrigatório
                'telefone': loja.owner_telefone or '',  # ✅ CORREÇÃO: Telefone do administrador para NF
                # ✅ CORREÇÃO v1320: Incluir endereço completo para emissão de NF
                'endereco': loja.logradouro or '',
                'numero': loja.numero or '',
                'complemento': loja.complemento or '',
                'bairro': loja.bairro or '',
                'cidade': loja.cidade or '',
                'estado': loja.uf or '',
                'cep': loja.cep or '',
                'slug': loja.slug
            }
            
            # Preparar dados do plano
            plano_data = {
                'nome': loja.plano.nome,
                'preco': float(financeiro.valor_mensalidade)
            }
            
            # Criar cobrança via serviço Asaas
            service = self.AsaasPaymentService()
            
            # Verificar se já existe customer_id no financeiro
            customer_id = financeiro.asaas_customer_id if financeiro.asaas_customer_id else None
            
            resultado = service.create_loja_subscription_payment(
                loja_data, 
                plano_data,
                customer_id=customer_id
            )
            
            if resultado.get('success'):
                # Atualizar financeiro com dados do Asaas
                financeiro.provedor_boleto = 'asaas'
                financeiro.mercadopago_payment_id = ''
                financeiro.asaas_customer_id = resultado.get('customer_id', '')
                financeiro.asaas_payment_id = resultado.get('payment_id', '')
                boleto_url_asaas = (resultado.get('boleto_url') or '')[:200]
                financeiro.boleto_url = boleto_url_asaas
                financeiro.pix_qr_code = (resultado.get('pix_qr_code') or '')[:500]
                financeiro.pix_copy_paste = (resultado.get('pix_copy_paste') or '')[:500]
                financeiro.status_pagamento = 'pendente'
                financeiro.save()
                
                # Criar registro de pagamento
                from .models import PagamentoLoja
                pagamento = PagamentoLoja.objects.create(
                    loja=loja,
                    financeiro=financeiro,
                    valor=financeiro.valor_mensalidade,
                    referencia_mes=financeiro.data_proxima_cobranca.replace(day=1),
                    status='pendente',
                    forma_pagamento='boleto',
                    data_vencimento=financeiro.data_proxima_cobranca,
                    provedor_boleto='asaas',
                    mercadopago_payment_id='',
                    asaas_payment_id=(resultado.get('payment_id') or '')[:100],
                    boleto_url=boleto_url_asaas,
                    pix_qr_code=(resultado.get('pix_qr_code') or '')[:500],
                    pix_copy_paste=(resultado.get('pix_copy_paste') or '')[:500]
                )
                
                logger.info(f"Cobrança Asaas criada para loja {loja.nome}: {resultado.get('payment_id')}")
                
                return {
                    'success': True,
                    'provedor': 'asaas',
                    'payment_id': resultado.get('payment_id'),
                    'customer_id': resultado.get('customer_id'),
                    'boleto_url': resultado.get('boleto_url'),
                    'pix_qr_code': resultado.get('pix_qr_code'),
                    'due_date': resultado.get('due_date'),
                    'value': resultado.get('value'),
                    'pagamento_id': pagamento.id
                }
            else:
                logger.error(f"Erro ao criar cobrança Asaas: {resultado.get('error')}")
                return {
                    'success': False,
                    'error': resultado.get('error', 'Erro desconhecido')
                }
                
        except Exception as e:
            logger.error(f"Erro no serviço Asaas: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def baixar_pdf_boleto(self, payment_id):
        """
        Baixa o PDF do boleto do Asaas
        
        Args:
            payment_id: ID do pagamento no Asaas
            
        Returns:
            bytes: Conteúdo do PDF ou None se erro
        """
        if not self.available:
            return None
        
        try:
            config = self.AsaasConfig.get_config()
            if not config.api_key or not config.enabled:
                return None
            
            service = self.AsaasPaymentService()
            return service.download_boleto_pdf(payment_id)
            
        except Exception as e:
            logger.error(f"Erro ao baixar PDF do boleto: {e}")
            return None
    
    def consultar_status_pagamento(self, payment_id):
        """
        Consulta status de um pagamento no Asaas
        
        Args:
            payment_id: ID do pagamento no Asaas
            
        Returns:
            dict: Status do pagamento
        """
        if not self.available:
            return {'success': False, 'error': 'Asaas não disponível'}
        
        try:
            config = self.AsaasConfig.get_config()
            if not config.api_key or not config.enabled:
                return {'success': False, 'error': 'Asaas não configurado'}
            
            service = self.AsaasPaymentService()
            return service.get_payment_status(payment_id)
            
        except Exception as e:
            logger.error(f"Erro ao consultar status: {e}")
            return {'success': False, 'error': str(e)}