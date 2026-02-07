"""
Serviço de sincronização automática com Asaas
Gerencia pagamentos, bloqueios e desbloqueios de lojas
"""
import logging
from datetime import datetime, timedelta, date
from django.utils import timezone
from django.db import transaction
from .models import Loja, FinanceiroLoja, PagamentoLoja
from .asaas_service import LojaAsaasService

logger = logging.getLogger(__name__)

class AsaasSyncService:
    """Serviço para sincronização automática com Asaas"""
    
    def __init__(self):
        self.asaas_service = LojaAsaasService()
        self.DAYS_TO_BLOCK = 5  # Dias de atraso para bloquear
        
    def sync_all_payments(self):
        """Sincroniza todos os pagamentos de todas as lojas"""
        logger.info("=== Iniciando sincronização completa com Asaas ===")
        
        if not self.asaas_service.available:
            logger.error("Serviço Asaas não disponível")
            return {
                'success': False,
                'error': 'Serviço Asaas não disponível'
            }
        
        # Buscar todas as lojas com integração Asaas
        lojas_com_asaas = Loja.objects.filter(
            is_active=True,
            financeiro__asaas_payment_id__isnull=False
        ).exclude(financeiro__asaas_payment_id='')
        
        total_lojas = lojas_com_asaas.count()
        sucessos = 0
        erros = 0
        bloqueadas = 0
        desbloqueadas = 0
        
        logger.info(f"Encontradas {total_lojas} lojas para sincronizar")
        
        for loja in lojas_com_asaas:
            try:
                resultado = self.sync_loja_payments(loja)
                
                if resultado['success']:
                    sucessos += 1
                    if resultado.get('blocked'):
                        bloqueadas += 1
                    if resultado.get('unblocked'):
                        desbloqueadas += 1
                else:
                    erros += 1
                    logger.error(f"Erro ao sincronizar loja {loja.nome}: {resultado.get('error')}")
                    
            except Exception as e:
                erros += 1
                logger.error(f"Erro inesperado ao sincronizar loja {loja.nome}: {e}")
        
        resultado_final = {
            'success': True,
            'total_lojas': total_lojas,
            'sucessos': sucessos,
            'erros': erros,
            'bloqueadas': bloqueadas,
            'desbloqueadas': desbloqueadas,
            'timestamp': timezone.now()
        }
        
        logger.info(f"Sincronização completa: {sucessos} sucessos, {erros} erros, {bloqueadas} bloqueadas, {desbloqueadas} desbloqueadas")
        
        return resultado_final
    
    def sync_loja_payments(self, loja):
        """Sincroniza pagamentos de uma loja específica"""
        try:
            financeiro = loja.financeiro
            
            # Buscar pagamentos pendentes da loja
            pagamentos_pendentes = PagamentoLoja.objects.filter(
                loja=loja,
                status__in=['pendente', 'atrasado'],
                asaas_payment_id__isnull=False
            ).exclude(asaas_payment_id='')
            
            pagamentos_atualizados = 0
            pagamento_pago = False
            
            # Sincronizar cada pagamento pendente
            for pagamento in pagamentos_pendentes:
                resultado_sync = self.sync_payment_status(pagamento)
                if resultado_sync['updated']:
                    pagamentos_atualizados += 1
                    if resultado_sync['status'] == 'pago':
                        pagamento_pago = True
            
            # Atualizar status da loja baseado nos pagamentos
            resultado_status = self.update_loja_status(loja, pagamento_pago)
            
            # Atualizar timestamp de sincronização
            financeiro.last_sync_at = timezone.now()
            financeiro.sync_error = ''
            financeiro.save()
            
            return {
                'success': True,
                'loja': loja.nome,
                'pagamentos_atualizados': pagamentos_atualizados,
                'blocked': resultado_status.get('blocked', False),
                'unblocked': resultado_status.get('unblocked', False),
                'status': loja.financeiro.status_pagamento
            }
            
        except Exception as e:
            # Salvar erro de sincronização
            try:
                financeiro = loja.financeiro
                financeiro.sync_error = str(e)
                financeiro.save()
            except:
                pass
            
            logger.error(f"Erro ao sincronizar loja {loja.nome}: {e}")
            return {
                'success': False,
                'error': str(e),
                'loja': loja.nome
            }
    
    def sync_payment_status(self, pagamento):
        """Sincroniza status de um pagamento específico"""
        try:
            # Consultar status no Asaas
            resultado = self.asaas_service.consultar_status_pagamento(pagamento.asaas_payment_id)
            
            if not resultado.get('success'):
                return {
                    'updated': False,
                    'error': resultado.get('error')
                }
            
            asaas_status = resultado.get('status', '')
            status_anterior = pagamento.status
            
            # Mapear status do Asaas para nosso sistema
            if asaas_status in ['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']:
                novo_status = 'pago'
                pagamento.data_pagamento = timezone.now()
                
                # Atualizar financeiro
                financeiro = pagamento.financeiro
                financeiro.ultimo_pagamento = timezone.now()
                financeiro.status_pagamento = 'ativo'
                financeiro.save()
                
            elif asaas_status == 'OVERDUE':
                novo_status = 'atrasado'
            else:
                novo_status = 'pendente'
            
            # Atualizar apenas se mudou
            if novo_status != status_anterior:
                pagamento.status = novo_status
                pagamento.save()
                
                logger.info(f"Pagamento {pagamento.id} atualizado: {status_anterior} -> {novo_status}")
                
                return {
                    'updated': True,
                    'status': novo_status,
                    'previous_status': status_anterior
                }
            
            return {
                'updated': False,
                'status': novo_status
            }
            
        except Exception as e:
            logger.error(f"Erro ao sincronizar pagamento {pagamento.id}: {e}")
            return {
                'updated': False,
                'error': str(e)
            }
    
    def update_loja_status(self, loja, pagamento_pago=False):
        """Atualiza status da loja baseado nos pagamentos"""
        try:
            financeiro = loja.financeiro
            hoje = date.today()
            
            # Se houve pagamento, desbloquear loja
            if pagamento_pago and loja.is_blocked:
                loja.is_blocked = False
                loja.blocked_at = None
                loja.blocked_reason = ''
                loja.days_overdue = 0
                loja.save()
                
                financeiro.status_pagamento = 'ativo'
                financeiro.save()
                
                logger.info(f"Loja {loja.nome} desbloqueada após pagamento")
                
                return {
                    'unblocked': True,
                    'status': 'ativo'
                }
            
            # Verificar se há pagamentos em atraso
            pagamentos_atrasados = PagamentoLoja.objects.filter(
                loja=loja,
                status='atrasado',
                data_vencimento__lt=hoje
            )
            
            if pagamentos_atrasados.exists():
                # Calcular dias de atraso
                pagamento_mais_antigo = pagamentos_atrasados.order_by('data_vencimento').first()
                dias_atraso = (hoje - pagamento_mais_antigo.data_vencimento).days
                
                loja.days_overdue = dias_atraso
                
                # Bloquear se passou de 5 dias
                if dias_atraso >= self.DAYS_TO_BLOCK and not loja.is_blocked:
                    loja.is_blocked = True
                    loja.blocked_at = timezone.now()
                    loja.blocked_reason = f'Inadimplência - {dias_atraso} dias de atraso'
                    loja.save()
                    
                    financeiro.status_pagamento = 'suspenso'
                    financeiro.save()
                    
                    logger.warning(f"Loja {loja.nome} bloqueada por {dias_atraso} dias de atraso")
                    
                    return {
                        'blocked': True,
                        'days_overdue': dias_atraso,
                        'status': 'suspenso'
                    }
                
                # Atualizar status para atrasado (mas não bloquear ainda)
                elif dias_atraso > 0:
                    loja.save()
                    financeiro.status_pagamento = 'atrasado'
                    financeiro.save()
                    
                    return {
                        'status': 'atrasado',
                        'days_overdue': dias_atraso
                    }
            
            else:
                # Não há pagamentos em atraso
                loja.days_overdue = 0
                loja.save()
                
                if not loja.is_blocked:
                    financeiro.status_pagamento = 'ativo'
                    financeiro.save()
            
            return {
                'status': financeiro.status_pagamento
            }
            
        except Exception as e:
            logger.error(f"Erro ao atualizar status da loja {loja.nome}: {e}")
            return {
                'error': str(e)
            }
    
    def process_webhook_payment(self, payment_data):
        """Processa notificação de webhook do Asaas"""
        try:
            payment_id = payment_data.get('id')
            event = payment_data.get('event')
            
            if not payment_id:
                return {
                    'success': False,
                    'error': 'ID do pagamento não fornecido'
                }
            
            # Buscar pagamento no sistema
            pagamento = None
            try:
                from asaas_integration.models import AsaasPayment
                pagamento = AsaasPayment.objects.get(asaas_id=payment_id)
                logger.info(f"Pagamento encontrado no AsaasPayment: {payment_id}")
            except AsaasPayment.DoesNotExist:
                # Se não encontrar no AsaasPayment, tentar no PagamentoLoja
                try:
                    pagamento = PagamentoLoja.objects.get(asaas_payment_id=payment_id)
                    logger.info(f"Pagamento encontrado no PagamentoLoja: {payment_id}")
                except PagamentoLoja.DoesNotExist:
                    # Pagamento não existe, tentar criar automaticamente
                    logger.warning(f"Pagamento {payment_id} não encontrado, tentando criar automaticamente")
                    
                    try:
                        pagamento = self._create_payment_from_webhook(payment_data)
                        if pagamento:
                            logger.info(f"Pagamento {payment_id} criado automaticamente via webhook")
                        else:
                            logger.error(f"Não foi possível criar pagamento {payment_id} automaticamente")
                            # Retornar sucesso para evitar reenvio do webhook
                            return {
                                'success': True,
                                'payment_id': payment_id,
                                'status': 'ignored',
                                'reason': 'Pagamento não encontrado e não foi possível criar automaticamente (loja ou cliente inexistente)'
                            }
                    except Exception as e:
                        logger.error(f"Erro ao criar pagamento automaticamente: {e}")
                        # Retornar sucesso para evitar reenvio do webhook
                        return {
                            'success': True,
                            'payment_id': payment_id,
                            'status': 'ignored',
                            'reason': f'Erro ao criar pagamento automaticamente: {str(e)}'
                        }
            
            if not pagamento:
                return {
                    'success': False,
                    'error': 'Pagamento não encontrado'
                }
            
            logger.info(f"Processando webhook para pagamento {payment_id}, evento: {event}")
            
            # Atualizar status do pagamento baseado nos dados do webhook
            old_status = pagamento.status
            new_status = payment_data.get('status', 'PENDING')
            
            if new_status != old_status:
                pagamento.status = new_status
                
                # Se foi pago, atualizar data de pagamento
                if new_status in ['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']:
                    pagamento.payment_date = timezone.now()
                
                pagamento.save()
                
                logger.info(f"Pagamento {payment_id} atualizado via webhook: {old_status} -> {new_status}")
                
                # IMPORTANTE: Atualizar financeiro da loja se o pagamento foi confirmado
                loja_atualizada = False
                loja = self._get_loja_from_payment(pagamento) if new_status in ['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH'] else None
                if new_status in ['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']:
                    try:
                        loja_atualizada = self._update_loja_financeiro_from_payment(pagamento)
                        if loja_atualizada:
                            logger.info(f"Financeiro da loja atualizado automaticamente via webhook")
                    except Exception as e:
                        logger.error(f"Erro ao atualizar financeiro da loja: {e}")
                    # Emissão de Nota Fiscal e envio por e-mail ao admin da loja
                    if loja:
                        try:
                            from asaas_integration.invoice_service import emitir_nf_para_pagamento
                            nf_value = float(payment_data.get('value', 0))
                            nf_description = payment_data.get('description') or f"Assinatura - {loja.nome}"
                            nf_result = emitir_nf_para_pagamento(
                                asaas_payment_id=payment_id,
                                loja=loja,
                                value=nf_value,
                                description=nf_description,
                                send_email=True,
                            )
                            if nf_result.get('success'):
                                logger.info(f"NF emitida para pagamento {payment_id}, e-mail enviado: {nf_result.get('email_sent')}")
                            else:
                                logger.warning(f"Falha ao emitir NF para {payment_id}: {nf_result.get('error')}")
                        except Exception as nf_err:
                            logger.exception(f"Erro ao emitir NF no webhook: {nf_err}")
                
                return {
                    'success': True,
                    'payment_id': payment_id,
                    'status_updated': True,
                    'old_status': old_status,
                    'new_status': new_status,
                    'loja_updated': loja_atualizada
                }
            
            return {
                'success': True,
                'payment_id': payment_id,
                'status_updated': False,
                'message': 'Status já atualizado'
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar webhook: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_payment_from_webhook(self, payment_data):
        """Cria pagamento automaticamente a partir dos dados do webhook"""
        try:
            from asaas_integration.models import AsaasPayment, AsaasCustomer
            from datetime import datetime
            
            # Extrair dados do pagamento
            payment_info = payment_data
            payment_id = payment_info.get('id')
            customer_id = payment_info.get('customer')
            external_reference = payment_info.get('externalReference', '')
            
            if not payment_id or not customer_id:
                logger.error("Dados insuficientes para criar pagamento automaticamente")
                return None
            
            # Verificar se a loja existe pelo external_reference
            if external_reference and 'loja_' in external_reference:
                loja_slug = external_reference.replace('loja_', '').replace('_assinatura', '')
                try:
                    loja = Loja.objects.get(slug=loja_slug, is_active=True)
                    logger.info(f"Loja encontrada para webhook: {loja.nome} ({loja_slug})")
                except Loja.DoesNotExist:
                    logger.warning(f"Loja {loja_slug} não encontrada - webhook ignorado")
                    return None
            else:
                logger.warning(f"External reference inválido: {external_reference} - webhook ignorado")
                return None
            
            # Buscar ou criar cliente
            customer = None
            try:
                customer = AsaasCustomer.objects.get(asaas_id=customer_id)
                logger.info(f"Cliente encontrado: {customer.name}")
            except AsaasCustomer.DoesNotExist:
                # Tentar criar cliente automaticamente se temos dados suficientes
                logger.warning(f"Cliente {customer_id} não encontrado - tentando criar automaticamente")
                
                # Para criar o cliente, precisamos de mais dados que não vêm no webhook
                # Por enquanto, vamos ignorar este webhook
                logger.warning(f"Não é possível criar cliente automaticamente - dados insuficientes")
                return None
            
            # Criar pagamento
            pagamento = AsaasPayment.objects.create(
                asaas_id=payment_id,
                customer=customer,
                external_reference=external_reference,
                billing_type=payment_info.get('billingType', 'BOLETO'),
                status=payment_info.get('status', 'PENDING'),
                value=payment_info.get('value', 0),
                net_value=payment_info.get('netValue', 0),
                due_date=datetime.strptime(payment_info.get('dueDate'), '%Y-%m-%d').date() if payment_info.get('dueDate') else None,
                invoice_url=payment_info.get('invoiceUrl', ''),
                bank_slip_url=payment_info.get('bankSlipUrl', ''),
                description=payment_info.get('description', ''),
                raw_data=payment_data
            )
            
            logger.info(f"Pagamento {payment_id} criado automaticamente via webhook")
            return pagamento
            
        except Exception as e:
            logger.error(f"Erro ao criar pagamento automaticamente: {e}")
            return None
    
    def _get_loja_from_payment(self, pagamento):
        """Retorna a Loja associada ao pagamento, ou None se não encontrar."""
        try:
            if hasattr(pagamento, 'loja'):
                return pagamento.loja
            if hasattr(pagamento, 'external_reference') and pagamento.external_reference:
                if 'loja_' in pagamento.external_reference:
                    loja_slug = pagamento.external_reference.replace('loja_', '').replace('_assinatura', '')
                    return Loja.objects.get(slug=loja_slug, is_active=True)
        except Loja.DoesNotExist:
            pass
        except Exception as e:
            logger.debug("_get_loja_from_payment: %s", e)
        return None

    def _update_loja_financeiro_from_payment(self, pagamento):
        """Atualiza financeiro da loja baseado no pagamento confirmado"""
        try:
            from datetime import date
            from calendar import monthrange
            
            logger.info(f"🔄 _update_loja_financeiro_from_payment iniciado para pagamento {pagamento.id}")
            logger.info(f"   - Asaas ID: {pagamento.asaas_id}")
            logger.info(f"   - Status: {pagamento.status}")
            logger.info(f"   - External Reference: {getattr(pagamento, 'external_reference', 'N/A')}")
            
            loja = self._get_loja_from_payment(pagamento)
            if not loja:
                logger.warning(f"❌ Não foi possível identificar a loja do pagamento {pagamento.id}")
                logger.warning(f"   - hasattr loja: {hasattr(pagamento, 'loja')}")
                logger.warning(f"   - hasattr external_reference: {hasattr(pagamento, 'external_reference')}")
                if hasattr(pagamento, 'external_reference'):
                    logger.warning(f"   - external_reference value: {pagamento.external_reference}")
                return False
            
            logger.info(f"✅ Loja identificada: {loja.nome} (slug: {loja.slug})")
            
            # Atualizar financeiro da loja
            financeiro = loja.financeiro
            
            logger.info(f"📊 Financeiro atual:")
            logger.info(f"   - Status: {financeiro.status_pagamento}")
            logger.info(f"   - Último Pagamento: {financeiro.ultimo_pagamento}")
            logger.info(f"   - Próxima Cobrança: {financeiro.data_proxima_cobranca}")
            logger.info(f"   - Dia Vencimento: {financeiro.dia_vencimento}")
            
            # Atualizar status para ativo
            financeiro.status_pagamento = 'ativo'
            financeiro.ultimo_pagamento = timezone.now()
            
            # Calcular próxima data de cobrança baseada no dia de vencimento
            hoje = date.today()
            dia_vencimento = financeiro.dia_vencimento
            
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
            
            # Definir próxima data de cobrança
            proxima_data_cobranca = date(proximo_ano, proximo_mes, dia_cobranca)
            
            logger.info(f"📅 Cálculo de próxima cobrança:")
            logger.info(f"   - Hoje: {hoje}")
            logger.info(f"   - Dia Vencimento: {dia_vencimento}")
            logger.info(f"   - Próximo Mês/Ano: {proximo_mes}/{proximo_ano}")
            logger.info(f"   - Próxima Cobrança Calculada: {proxima_data_cobranca}")
            logger.info(f"   - Próxima Cobrança Anterior: {financeiro.data_proxima_cobranca}")
            
            financeiro.data_proxima_cobranca = proxima_data_cobranca
            
            financeiro.save()
            logger.info(f"✅ Financeiro salvo com nova data: {proxima_data_cobranca}")
            
            # Criar próximo boleto no Asaas automaticamente
            try:
                from asaas_integration.models import LojaAssinatura, AsaasPayment
                from asaas_integration.client import AsaasPaymentService
                
                logger.info(f"🔍 Buscando LojaAssinatura para slug: {loja.slug}")
                loja_assinatura = LojaAssinatura.objects.get(loja_slug=loja.slug)
                logger.info(f"✅ LojaAssinatura encontrada")
                
                # Atualizar data_vencimento da assinatura
                logger.info(f"📝 Atualizando data_vencimento: {loja_assinatura.data_vencimento} → {proxima_data_cobranca}")
                loja_assinatura.data_vencimento = proxima_data_cobranca
                loja_assinatura.save()
                logger.info(f"✅ LojaAssinatura.data_vencimento atualizada para {proxima_data_cobranca}")
                
                # Verificar se já existe cobrança para essa data (evitar duplicação)
                logger.info(f"🔍 Verificando cobranças existentes para {proxima_data_cobranca}...")
                cobranca_existente = AsaasPayment.objects.filter(
                    customer=loja_assinatura.asaas_customer,
                    due_date=proxima_data_cobranca,
                    status__in=['PENDING', 'RECEIVED', 'CONFIRMED']
                ).exists()
                
                if cobranca_existente:
                    logger.info(f"⚠️ Já existe cobrança para {proxima_data_cobranca}, pulando criação")
                else:
                    logger.info(f"✅ Nenhuma cobrança existente, criando novo boleto...")
                    
                    # Criar novo boleto no Asaas para o próximo mês
                    asaas_service = AsaasPaymentService()
                    
                    # Preparar dados para nova cobrança
                    loja_data = {
                        'nome': loja.nome,
                        'slug': loja.slug,
                        'email': loja.owner.email,
                        'cpf_cnpj': loja.cpf_cnpj or '000.000.000-00',
                        'telefone': getattr(loja.owner, 'telefone', ''),
                    }
                    
                    valor_plano = loja.plano.preco_anual if loja.tipo_assinatura == 'anual' else loja.plano.preco_mensal
                    plano_data = {
                        'nome': f"{loja.plano.nome} ({loja.get_tipo_assinatura_display()})",
                        'preco': valor_plano
                    }
                    
                    logger.info(f"💰 Dados da cobrança:")
                    logger.info(f"   - Loja: {loja_data['nome']}")
                    logger.info(f"   - Plano: {plano_data['nome']}")
                    logger.info(f"   - Valor: R$ {plano_data['preco']}")
                    logger.info(f"   - Vencimento: {proxima_data_cobranca}")
                    
                    # Criar cobrança no Asaas com vencimento no próximo mês
                    due_date_str = proxima_data_cobranca.strftime('%Y-%m-%d')
                    logger.info(f"🚀 Chamando Asaas API para criar cobrança...")
                    result = asaas_service.create_loja_subscription_payment(loja_data, plano_data, due_date=due_date_str)
                    
                    if result['success']:
                        logger.info(f"✅ Cobrança criada no Asaas com sucesso!")
                        logger.info(f"   - Payment ID: {result['payment_id']}")
                        logger.info(f"   - Status: {result['status']}")
                        logger.info(f"   - Valor: R$ {result['value']}")
                        logger.info(f"   - Vencimento: {result['due_date']}")
                        
                        # Criar novo pagamento no banco local
                        from datetime import datetime
                        new_payment = AsaasPayment.objects.create(
                            asaas_id=result['payment_id'],
                            customer=loja_assinatura.asaas_customer,
                            external_reference=f"loja_{loja.slug}_assinatura_{proxima_data_cobranca.strftime('%Y%m')}",
                            billing_type='BOLETO',
                            status=result['status'],
                            value=result['value'],
                            due_date=datetime.strptime(result['due_date'], '%Y-%m-%d').date(),
                            invoice_url=result['payment_url'],
                            bank_slip_url=result['boleto_url'],
                            pix_qr_code=result['pix_qr_code'],
                            pix_copy_paste=result['pix_copy_paste'],
                            description=f"Assinatura {plano_data['nome']} - Loja {loja.nome} - {proxima_data_cobranca.strftime('%m/%Y')}",
                            raw_data=result['raw_payment']
                        )
                        
                        logger.info(f"✅ Pagamento criado no banco local (ID: {new_payment.id})")
                        
                        # Atualizar current_payment da assinatura
                        loja_assinatura.current_payment = new_payment
                        loja_assinatura.save()
                        
                        logger.info(f"✅ Novo boleto criado no Asaas para {loja.nome}: Vencimento {proxima_data_cobranca}")
                    else:
                        logger.error(f"❌ Erro ao criar novo boleto no Asaas: {result.get('error')}")
                    
            except LojaAssinatura.DoesNotExist:
                logger.warning(f"❌ LojaAssinatura não encontrada para loja {loja.slug}")
            except Exception as e:
                logger.error(f"❌ Erro ao criar próximo boleto: {e}")
                import traceback
                traceback.print_exc()
            
            # Desbloquear loja se estiver bloqueada
            if loja.is_blocked:
                loja.is_blocked = False
                loja.blocked_at = None
                loja.blocked_reason = ''
                loja.days_overdue = 0
                loja.save()
                logger.info(f"✅ Loja {loja.nome} desbloqueada automaticamente após pagamento")
            
            logger.info(
                f"✅ Financeiro da loja {loja.nome} atualizado: "
                f"status={financeiro.status_pagamento}, "
                f"próxima_cobrança={financeiro.data_proxima_cobranca}"
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar financeiro da loja: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_sync_stats(self):
        """Retorna estatísticas de sincronização"""
        try:
            total_lojas = Loja.objects.filter(is_active=True).count()
            lojas_com_asaas = Loja.objects.filter(
                is_active=True,
                financeiro__asaas_payment_id__isnull=False
            ).exclude(financeiro__asaas_payment_id='').count()
            
            lojas_bloqueadas = Loja.objects.filter(
                is_active=True,
                is_blocked=True
            ).count()
            
            pagamentos_pendentes = PagamentoLoja.objects.filter(
                status__in=['pendente', 'atrasado']
            ).count()
            
            pagamentos_pagos_hoje = PagamentoLoja.objects.filter(
                status='pago',
                data_pagamento__date=date.today()
            ).count()
            
            return {
                'total_lojas': total_lojas,
                'lojas_com_asaas': lojas_com_asaas,
                'lojas_bloqueadas': lojas_bloqueadas,
                'pagamentos_pendentes': pagamentos_pendentes,
                'pagamentos_pagos_hoje': pagamentos_pagos_hoje,
                'ultima_sincronizacao': timezone.now()
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {
                'error': str(e)
            }