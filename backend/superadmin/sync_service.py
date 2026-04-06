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
                    # Extrair slug da loja do external_reference
                    # Formato: loja_luiz-salao-5889_assinatura_202604
                    # Resultado esperado: luiz-salao-5889
                    import re
                    match = re.search(r'loja_([^_]+(?:_\d+)?)', pagamento.external_reference)
                    if match:
                        loja_slug = match.group(1)
                        logger.info(f"🔍 Slug extraído do external_reference: {loja_slug}")
                        return Loja.objects.get(slug=loja_slug, is_active=True)
        except Loja.DoesNotExist:
            logger.warning(f"❌ Loja não encontrada com slug: {loja_slug}")
        except Exception as e:
            logger.error(f"❌ Erro ao extrair loja do pagamento: {e}")
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
            
            # ✅ MODIFICAÇÃO: Calcular próxima data de cobrança baseada no tipo de assinatura
            # Mensal: 30 dias após pagamento | Anual: 365 dias após pagamento
            data_pagamento = timezone.now().date()  # Data em que o pagamento foi confirmado
            dia_vencimento = financeiro.dia_vencimento
            tipo_assinatura = loja.tipo_assinatura
            
            logger.info(f"📅 Cálculo de próxima cobrança:")
            logger.info(f"   - Data do Pagamento: {data_pagamento}")
            logger.info(f"   - Dia Vencimento Configurado: {dia_vencimento}")
            logger.info(f"   - Tipo de Assinatura: {tipo_assinatura}")
            
            # Calcular próxima data de cobrança baseada no tipo de assinatura
            if tipo_assinatura == 'anual':
                dias_adicionar = 365
                proxima_data_cobranca = data_pagamento + timedelta(days=dias_adicionar)
            else:  # mensal
                dias_adicionar = 30
                proxima_data_cobranca = data_pagamento + timedelta(days=dias_adicionar)
            
            logger.info(f"   - Próxima Cobrança Calculada ({dias_adicionar} dias após pagamento): {proxima_data_cobranca}")
            logger.info(f"   - Diferença: {data_pagamento} → {proxima_data_cobranca} ({dias_adicionar} dias)")
            
            financeiro.data_proxima_cobranca = proxima_data_cobranca
            
            financeiro.save()
            logger.info(f"✅ Financeiro salvo com nova data: {proxima_data_cobranca}")
            
            # ✅ ALTERAÇÃO v1479: NÃO criar boleto imediatamente após pagamento
            # O boleto será criado automaticamente 10 dias antes do vencimento
            # via comando: python manage.py criar_boletos_proximos
            
            # Apenas atualizar data_vencimento da assinatura
            try:
                from asaas_integration.models import LojaAssinatura
                
                logger.info(f"🔍 Buscando LojaAssinatura para slug: {loja.slug}")
                loja_assinatura = LojaAssinatura.objects.get(loja_slug=loja.slug)
                logger.info(f"✅ LojaAssinatura encontrada")
                
                # Atualizar data_vencimento da assinatura
                logger.info(f"📝 Atualizando data_vencimento: {loja_assinatura.data_vencimento} → {proxima_data_cobranca}")
                loja_assinatura.data_vencimento = proxima_data_cobranca
                loja_assinatura.save()
                logger.info(f"✅ LojaAssinatura.data_vencimento atualizada para {proxima_data_cobranca}")
                logger.info(f"📧 Boleto será criado e enviado automaticamente 10 dias antes do vencimento")
                    
            except LojaAssinatura.DoesNotExist:
                logger.warning(f"❌ LojaAssinatura não encontrada para loja {loja.slug}")
            except Exception as e:
                logger.error(f"❌ Erro ao atualizar LojaAssinatura: {e}")
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


def sync_all_mercadopago_payments():
    """
    Sincroniza todos os pagamentos pendentes do Mercado Pago (consulta a API e atualiza status).
    Pode ser executado periodicamente no servidor (ex.: Heroku Scheduler a cada 10 min) para
    atualização em tempo real, similar ao sync do Asaas.
    """
    from .models import MercadoPagoConfig
    config = MercadoPagoConfig.get_config()
    if not config or not config.access_token:
        logger.warning("Mercado Pago não configurado; sync ignorado")
        return {'success': False, 'error': 'Mercado Pago não configurado', 'processed': 0}

    # IDs de pagamento pendentes em PagamentoLoja (boleto + PIX)
    ids_pagamento = set()
    for row in PagamentoLoja.objects.filter(
        provedor_boleto='mercadopago',
        status__in=['pendente', 'atrasado'],
    ).values_list('mercadopago_payment_id', 'mercadopago_pix_payment_id'):
        for pid in row:
            if pid:
                ids_pagamento.add(pid)
    # IDs em FinanceiroLoja (cobrança atual)
    ids_financeiro = set()
    for row in FinanceiroLoja.objects.filter(
        provedor_boleto='mercadopago',
    ).values_list('mercadopago_payment_id', 'mercadopago_pix_payment_id'):
        for pid in row:
            if pid:
                ids_financeiro.add(pid)
    payment_ids = list(ids_pagamento | ids_financeiro)
    if not payment_ids:
        logger.info("Sync MP: nenhum pagamento pendente com Mercado Pago")
        return {'success': True, 'processed': 0, 'total_checked': 0}

    processed = 0
    for pid in payment_ids:
        try:
            result = process_mercadopago_webhook_payment(str(pid))
            if result.get('processed'):
                processed += 1
        except Exception as e:
            logger.warning("Sync MP: erro ao processar payment %s: %s", pid, e)

    logger.info("Sync MP: %d pagamentos verificados, %d atualizados", len(payment_ids), processed)
    return {
        'success': True,
        'total_checked': len(payment_ids),
        'processed': processed,
    }


def sync_loja_payments_mercadopago(loja):
    """Sincroniza pagamentos Mercado Pago de uma loja específica (boleto + PIX)."""
    ids_pagamento = set()
    for row in PagamentoLoja.objects.filter(
        loja=loja,
        provedor_boleto='mercadopago',
        status__in=['pendente', 'atrasado'],
    ).values_list('mercadopago_payment_id', 'mercadopago_pix_payment_id'):
        for pid in row:
            if pid:
                ids_pagamento.add(pid)
    try:
        financeiro = loja.financeiro
        if getattr(financeiro, 'provedor_boleto', '') == 'mercadopago':
            if getattr(financeiro, 'mercadopago_payment_id', ''):
                ids_pagamento.add(financeiro.mercadopago_payment_id)
            if getattr(financeiro, 'mercadopago_pix_payment_id', ''):
                ids_pagamento.add(financeiro.mercadopago_pix_payment_id)
    except Exception:
        pass
    processed = 0
    for pid in ids_pagamento:
        try:
            result = process_mercadopago_webhook_payment(str(pid), loja=loja)
            if result.get('processed'):
                processed += 1
        except Exception as e:
            logger.warning("Sync MP loja %s payment %s: %s", loja.slug, pid, e)
    return {'success': True, 'loja': loja.nome, 'processed': processed, 'total_checked': len(ids_pagamento)}


def process_mercadopago_webhook_payment(payment_id: str, loja=None) -> dict:
    """
    Processa notificação de webhook do Mercado Pago.
    Quando o pagamento está aprovado, atualiza PagamentoLoja e FinanceiroLoja
    (status ativo, próxima cobrança, desbloqueia loja).
    """
    from calendar import monthrange
    from .models import MercadoPagoConfig
    from .mercadopago_service import MercadoPagoClient

    if not payment_id:
        return {'success': False, 'error': 'payment_id obrigatório'}

    config = MercadoPagoConfig.get_config()
    if not config or not config.access_token:
        return {'success': False, 'error': 'Mercado Pago não configurado'}

    client = MercadoPagoClient(config.access_token)
    payment_data = client.get_payment(str(payment_id))
    if not payment_data:
        return {'success': False, 'error': f'Pagamento {payment_id} não encontrado na API do Mercado Pago'}

    status_mp = payment_data.get('status', '')
    if status_mp != 'approved':
        logger.info(f"Webhook MP pagamento {payment_id} status={status_mp}, ignorando (aguardando approved)")
        return {'success': True, 'processed': False, 'status': status_mp}

    # Buscar PagamentoLoja pelo ID do Mercado Pago (boleto ou PIX).
    # Se loja for passada (sync por loja), restringe àquela loja para não marcar outra como paga por engano.
    from django.db.models import Q
    q_payment = Q(mercadopago_payment_id=str(payment_id)) | Q(mercadopago_pix_payment_id=str(payment_id))
    base_qs = PagamentoLoja.objects.filter(q_payment, provedor_boleto='mercadopago')
    if loja is not None:
        base_qs = base_qs.filter(loja=loja)
    pagamento = base_qs.first()
    if base_qs.count() > 1 and loja is None:
        logger.warning(
            "Webhook MP: payment_id %s vinculado a mais de uma loja (%s). "
            "Atualizando apenas a primeira; corrija os dados para evitar duplicidade.",
            payment_id, list(base_qs.values_list('loja__slug', flat=True)),
        )
    if pagamento is None:
        # Pode ser a cobrança atual só no FinanceiroLoja (primeira cobrança)
        try:
            fin_qs = FinanceiroLoja.objects.filter(
                q_payment,
                provedor_boleto='mercadopago',
            )
            if loja is not None:
                fin_qs = fin_qs.filter(loja=loja)
            financeiro = fin_qs.first()
            if not financeiro:
                raise FinanceiroLoja.DoesNotExist
            loja = financeiro.loja
            # Marcar PagamentoLoja correspondente ou criar registro de pagamento
            pagamento = PagamentoLoja.objects.filter(loja=loja).filter(
                Q(mercadopago_payment_id=str(payment_id)) | Q(mercadopago_pix_payment_id=str(payment_id)),
            ).first()
            if not pagamento:
                pagamento = PagamentoLoja.objects.filter(
                    loja=loja, financeiro=financeiro, status='pendente', provedor_boleto='mercadopago'
                ).order_by('-data_vencimento').first()
            if pagamento and pagamento.status == 'pendente':
                pagamento.status = 'pago'
                pagamento.data_pagamento = timezone.now()
                if not pagamento.mercadopago_payment_id:
                    pagamento.mercadopago_payment_id = str(payment_id)
                if not pagamento.mercadopago_pix_payment_id and pagamento.mercadopago_payment_id != str(payment_id):
                    pagamento.mercadopago_pix_payment_id = str(payment_id)
                pagamento.save(update_fields=['status', 'data_pagamento', 'mercadopago_payment_id', 'mercadopago_pix_payment_id'])
            financeiro = loja.financeiro
            _update_loja_financeiro_after_mercadopago_payment(loja, financeiro)
            if getattr(loja, 'is_blocked', False):
                loja.is_blocked = False
                loja.blocked_at = None
                loja.blocked_reason = ''
                loja.days_overdue = 0
                loja.save(update_fields=['is_blocked', 'blocked_at', 'blocked_reason', 'days_overdue'])
            logger.info(f"Financeiro da loja {loja.nome} atualizado via webhook MP (payment {payment_id})")
            return {'success': True, 'processed': True, 'loja_slug': loja.slug}
        except FinanceiroLoja.DoesNotExist:
            logger.warning(f"Webhook MP: pagamento {payment_id} não encontrado em PagamentoLoja nem em FinanceiroLoja")
            return {'success': True, 'processed': False, 'error': 'Pagamento não vinculado a nenhuma loja'}

    if pagamento.status == 'pago':
        return {'success': True, 'processed': False, 'message': 'Pagamento já estava pago'}

    pagamento.status = 'pago'
    pagamento.data_pagamento = timezone.now()
    pagamento.save(update_fields=['status', 'data_pagamento'])
    loja = pagamento.loja
    financeiro = loja.financeiro
    _update_loja_financeiro_after_mercadopago_payment(loja, financeiro)
    if getattr(loja, 'is_blocked', False):
        loja.is_blocked = False
        loja.blocked_at = None
        loja.blocked_reason = ''
        loja.days_overdue = 0
        loja.save(update_fields=['is_blocked', 'blocked_at', 'blocked_reason', 'days_overdue'])
    logger.info(f"Pagamento MP {payment_id} marcado como pago; financeiro da loja {loja.nome} atualizado")
    return {'success': True, 'processed': True, 'loja_slug': loja.slug}


def _update_loja_financeiro_after_mercadopago_payment(loja, financeiro):
    """
    Atualiza status e próxima cobrança do financeiro após pagamento aprovado no Mercado Pago.
    
    ✅ MODIFICAÇÃO v728: Removido update_fields para garantir que signal on_payment_confirmed seja disparado.
    O signal on_payment_confirmed envia a senha provisória automaticamente.
    
    ✅ MODIFICAÇÃO v729: Cancelar automaticamente a transação não paga (boleto ou PIX).
    Quando PIX é pago, cancela o boleto. Quando boleto é pago, cancela o PIX.
    
    ✅ MODIFICAÇÃO v735: Criar automaticamente o próximo boleto após pagamento confirmado.
    """
    from calendar import monthrange
    financeiro.status_pagamento = 'ativo'
    financeiro.ultimo_pagamento = timezone.now()
    data_vencimento_atual = financeiro.data_proxima_cobranca
    dia_vencimento = getattr(financeiro, 'dia_vencimento', 10) or 10
    if data_vencimento_atual.month == 12:
        proximo_mes, proximo_ano = 1, data_vencimento_atual.year + 1
    else:
        proximo_mes, proximo_ano = data_vencimento_atual.month + 1, data_vencimento_atual.year
    ultimo_dia = monthrange(proximo_ano, proximo_mes)[1]
    dia_cobranca = min(dia_vencimento, ultimo_dia)
    financeiro.data_proxima_cobranca = date(proximo_ano, proximo_mes, dia_cobranca)
    # ✅ Removido update_fields para disparar signal on_payment_confirmed
    financeiro.save()
    
    # ✅ NOVO v729: Cancelar transação não paga no Mercado Pago
    try:
        from .models import MercadoPagoConfig
        from .mercadopago_service import MercadoPagoClient
        
        config = MercadoPagoConfig.get_config()
        if config and config.access_token:
            client = MercadoPagoClient(config.access_token)
            
            # Identificar qual transação foi paga e qual deve ser cancelada
            boleto_id = getattr(financeiro, 'mercadopago_payment_id', None)
            pix_id = getattr(financeiro, 'mercadopago_pix_payment_id', None)
            
            if boleto_id and pix_id:
                # Verificar qual foi pago
                boleto_data = client.get_payment(str(boleto_id))
                pix_data = client.get_payment(str(pix_id))
                
                boleto_status = (boleto_data.get('status') if boleto_data else None) or ''
                pix_status = (pix_data.get('status') if pix_data else None) or ''
                
                # Se PIX foi aprovado, cancelar boleto
                if pix_status == 'approved' and boleto_status in ('pending', 'in_process'):
                    logger.info(f"PIX aprovado para loja {loja.slug}. Cancelando boleto {boleto_id}...")
                    if client.cancel_payment(str(boleto_id)):
                        logger.info(f"✅ Boleto {boleto_id} cancelado automaticamente")
                    else:
                        logger.warning(f"⚠️ Não foi possível cancelar boleto {boleto_id}")
                
                # Se boleto foi aprovado, cancelar PIX
                elif boleto_status == 'approved' and pix_status in ('pending', 'in_process'):
                    logger.info(f"Boleto aprovado para loja {loja.slug}. Cancelando PIX {pix_id}...")
                    if client.cancel_payment(str(pix_id)):
                        logger.info(f"✅ PIX {pix_id} cancelado automaticamente")
                    else:
                        logger.warning(f"⚠️ Não foi possível cancelar PIX {pix_id}")
    
    except Exception as e:
        logger.warning(f"Erro ao cancelar transação não paga para loja {loja.slug}: {e}")
    
    # ✅ NOVO v735: Criar próximo boleto automaticamente
    try:
        from .cobranca_service import CobrancaService
        
        logger.info(f"Criando próximo boleto para loja {loja.slug} (vencimento: {financeiro.data_proxima_cobranca})")
        
        service = CobrancaService()
        result = service.renovar_cobranca(loja, financeiro, dia_vencimento)
        
        if result.get('success'):
            logger.info(f"✅ Próximo boleto criado para loja {loja.slug}: {result.get('payment_id')}")
        else:
            logger.warning(f"⚠️ Erro ao criar próximo boleto para loja {loja.slug}: {result.get('error')}")
    
    except Exception as e:
        logger.warning(f"Erro ao criar próximo boleto para loja {loja.slug}: {e}")