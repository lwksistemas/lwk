"""Sincronização com Mercado Pago."""
import logging

from django.utils import timezone

from ..models import FinanceiroLoja, PagamentoLoja
from .nfse import tentar_emitir_nfse_assinatura

logger = logging.getLogger(__name__)

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
    from .mercadopago_service import MercadoPagoClient
    from .models import MercadoPagoConfig

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
            tentar_emitir_nfse_assinatura(pagamento, payment_id)
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
    tentar_emitir_nfse_assinatura(pagamento, payment_id)
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
    from superadmin.services import FinanceiroService

    financeiro.status_pagamento = 'ativo'
    financeiro.ultimo_pagamento = timezone.now()
    data_pagamento = timezone.now().date()
    financeiro.data_proxima_cobranca = FinanceiroService.calcular_proxima_cobranca_apos_pagamento(
        financeiro, loja, data_pagamento
    )
    # ✅ Removido update_fields para disparar signal on_payment_confirmed
    financeiro.save()
    
    # ✅ NOVO v729: Cancelar transação não paga no Mercado Pago
    try:
        from .mercadopago_service import MercadoPagoClient
        from .models import MercadoPagoConfig
        
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
        
        dia_vencimento = getattr(financeiro, 'dia_vencimento', None)
        service = CobrancaService()
        result = service.renovar_cobranca(loja, financeiro, dia_vencimento)
        
        if result.get('success'):
            logger.info(f"✅ Próximo boleto criado para loja {loja.slug}: {result.get('payment_id')}")
        else:
            logger.warning(f"⚠️ Erro ao criar próximo boleto para loja {loja.slug}: {result.get('error')}")
    
    except Exception as e:
        logger.warning(f"Erro ao criar próximo boleto para loja {loja.slug}: {e}")
