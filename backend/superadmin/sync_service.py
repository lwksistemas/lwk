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
                    logger.warning(f"Pagamento {payment_id} não encontrado em nenhum modelo")
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
                
                return {
                    'success': True,
                    'payment_id': payment_id,
                    'status_updated': True,
                    'old_status': old_status,
                    'new_status': new_status
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