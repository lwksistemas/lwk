"""Painel financeiro unificado (superadmin)."""
import logging

from django.db import models
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import FinanceiroLoja, PagamentoLoja

logger = logging.getLogger(__name__)

def _financeiro_unificado_stats():
    """Estatísticas unificadas (Asaas + Mercado Pago) para superadmin."""
    from decimal import Decimal

    from django.db.models import Sum

    from asaas_integration.models import AsaasPayment, LojaAssinatura

    # Asaas (AsaasPayment local)
    total_asaas = LojaAssinatura.objects.count()
    ativas_asaas = LojaAssinatura.objects.filter(ativa=True).count()
    pag_asaas = AsaasPayment.objects
    pagos_asaas_count = pag_asaas.filter(status__in=['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']).count()
    vencidos_asaas = pag_asaas.filter(status='OVERDUE').count()
    receita_asaas = pag_asaas.filter(status__in=['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']).aggregate(t=Sum('value'))['t'] or Decimal('0')
    pendente_asaas = pag_asaas.filter(status__in=['PENDING', 'OVERDUE']).aggregate(t=Sum('value'))['t'] or Decimal('0')
    pendentes_asaas_count = pag_asaas.filter(status='PENDING').count()

    # PagamentoLoja pagos que não estão no AsaasPayment (pagamentos antigos)
    asaas_ids_locais = set(pag_asaas.values_list('asaas_id', flat=True))
    pl_pagos = PagamentoLoja.objects.filter(status='pago').exclude(asaas_payment_id__in=asaas_ids_locais)
    receita_pl = pl_pagos.aggregate(t=Sum('valor'))['t'] or Decimal('0')
    pagos_pl_count = pl_pagos.count()

    # Mercado Pago (FinanceiroLoja com boleto MP)
    mp_fin = FinanceiroLoja.objects.filter(provedor_boleto='mercadopago', mercadopago_payment_id__isnull=False).exclude(mercadopago_payment_id='')
    total_mp = mp_fin.count()
    pendente_mp = sum(f.valor_mensalidade for f in mp_fin)

    return {
        'total_assinaturas': total_asaas + total_mp,
        'assinaturas_ativas': ativas_asaas + total_mp,
        'pagamentos_pendentes': pendentes_asaas_count + total_mp,
        'pagamentos_pagos': pagos_asaas_count + pagos_pl_count,
        'pagamentos_vencidos': vencidos_asaas,
        'receita_total': float(receita_asaas + receita_pl),
        'receita_pendente': float(pendente_asaas) + float(pendente_mp),
    }


def _assinaturas_unificado():
    """Lista unificada de assinaturas (Asaas + Mercado Pago) no formato esperado pelo frontend."""
    from asaas_integration.models import AsaasPayment, LojaAssinatura
    from asaas_integration.serializers import LojaAssinaturaSerializer

    out = []
    # Asaas
    for a in LojaAssinatura.objects.all().select_related('asaas_customer', 'current_payment').order_by('-created_at'):
        data = LojaAssinaturaSerializer(a).data

        # Histórico: combinar AsaasPayment + PagamentoLoja para cobrir todos os cenários
        history = []
        seen_asaas_ids = set()

        # 1) AsaasPayment (pagamentos registrados no Asaas local)
        ap_qs = AsaasPayment.objects.filter(
            models.Q(external_reference__contains=f"loja_{a.loja_slug}") |
            models.Q(customer=a.asaas_customer)
        ).order_by('-due_date').distinct()[:20]
        for p in ap_qs:
            seen_asaas_ids.add(p.asaas_id)
            history.append({
                'id': p.id,
                'asaas_id': p.asaas_id,
                'value': str(p.value),
                'status': p.status,
                'status_display': p.get_status_display(),
                'due_date': p.due_date.strftime('%Y-%m-%d') if p.due_date else None,
                'payment_date': p.payment_date.strftime('%Y-%m-%d') if p.payment_date else None,
                'is_paid': p.is_paid,
                'bank_slip_url': p.bank_slip_url or '',
            })

        # 2) PagamentoLoja (histórico local que pode ter pagamentos não presentes no AsaasPayment)
        try:
            from superadmin.models import Loja as LojaModel
            loja_obj = LojaModel.objects.filter(slug=a.loja_slug).first()
            if loja_obj:
                for pl in PagamentoLoja.objects.filter(loja=loja_obj).order_by('-data_vencimento')[:20]:
                    aid = pl.asaas_payment_id or ''
                    if aid and aid in seen_asaas_ids:
                        continue  # já incluído via AsaasPayment
                    status_map = {'pago': 'RECEIVED', 'pendente': 'PENDING', 'atrasado': 'OVERDUE', 'cancelado': 'REFUNDED'}
                    history.append({
                        'id': pl.id,
                        'asaas_id': aid,
                        'value': str(pl.valor),
                        'status': status_map.get(pl.status, 'PENDING'),
                        'status_display': pl.get_status_display(),
                        'due_date': pl.data_vencimento.strftime('%Y-%m-%d') if pl.data_vencimento else None,
                        'payment_date': pl.data_pagamento.strftime('%Y-%m-%d') if pl.data_pagamento else None,
                        'is_paid': pl.status == 'pago',
                        'bank_slip_url': pl.boleto_url or '',
                    })
        except Exception:
            pass

        # Ordenar por data de vencimento (mais recente primeiro)
        history.sort(key=lambda x: x.get('due_date') or '', reverse=True)
        data['payment_history'] = history[:20]
        out.append(data)
    # Mercado Pago (FinanceiroLoja com boleto)
    for f in FinanceiroLoja.objects.filter(
        provedor_boleto='mercadopago'
    ).exclude(mercadopago_payment_id='').select_related('loja', 'loja__plano'):
        loja = f.loja
        data_venc = f.data_proxima_cobranca.strftime('%Y-%m-%d') if f.data_proxima_cobranca else ''
        # ID do PagamentoLoja (pendente ou último) para o endpoint baixar_boleto_pdf
        pagamento_atual = (
            PagamentoLoja.objects.filter(loja=loja, financeiro=f, status='pendente')
            .order_by('-data_vencimento')
            .first()
        )
        if not pagamento_atual:
            pagamento_atual = (
                PagamentoLoja.objects.filter(loja=loja, financeiro=f)
                .order_by('-data_vencimento')
                .first()
            )
        payment_pk = pagamento_atual.id if pagamento_atual else None
        # PIX: preferir do PagamentoLoja (pagamento atual), senão do FinanceiroLoja
        pix_cp = ''
        pix_qr = ''
        if pagamento_atual and (pagamento_atual.pix_copy_paste or pagamento_atual.pix_qr_code):
            pix_cp = pagamento_atual.pix_copy_paste or ''
            pix_qr = pagamento_atual.pix_qr_code or ''
        else:
            pix_cp = f.pix_copy_paste or ''
            pix_qr = f.pix_qr_code or ''
        # Status real: pagamento_atual.status (pago/pendente/atrasado)
        is_pago = pagamento_atual and getattr(pagamento_atual, 'status', '') == 'pago'
        status_mp = 'RECEIVED' if is_pago else 'PENDING'
        status_display_mp = 'Pago' if is_pago else 'Pendente'
        
        # ✅ NOVO v730: Status da assinatura (não do próximo pagamento)
        subscription_status = 'active' if f.status_pagamento == 'ativo' else 'inactive'
        subscription_status_display = 'Ativo' if f.status_pagamento == 'ativo' else 'Inativo'
        
        out.append({
            'id': f'mp-{f.id}',
            'loja_slug': loja.slug,
            'loja_nome': loja.nome,
            'plano_nome': loja.plano.nome if loja.plano else 'Plano',
            'plano_valor': str(f.valor_mensalidade),
            'ativa': f.status_pagamento == 'ativo',  # ✅ Baseado no status real
            'subscription_status': subscription_status,  # ✅ NOVO v730
            'subscription_status_display': subscription_status_display,  # ✅ NOVO v730
            'data_vencimento': data_venc,
            'total_payments': 1,
            'financeiro_id': f.id,
            'current_payment_data': {
                'id': payment_pk,
                'asaas_id': f.mercadopago_payment_id,
                'provedor': 'mercadopago',
                'customer_name': loja.nome,
                'value': str(f.valor_mensalidade),
                'status': status_mp,
                'status_display': status_display_mp,
                'due_date': data_venc,
                'bank_slip_url': f.boleto_url or '',
                'pix_copy_paste': pix_cp,
                'pix_qr_code': pix_qr or None,
                'is_paid': is_pago,
                'is_pending': not is_pago,
                'is_overdue': False,
            },
            'payment_history': [
                {
                    'id': p.id,
                    'asaas_id': p.mercadopago_payment_id or p.asaas_payment_id or '',
                    'value': str(p.valor),
                    'status': 'RECEIVED' if p.status == 'pago' else 'PENDING' if p.status == 'pendente' else 'OVERDUE',
                    'status_display': p.get_status_display(),
                    'due_date': p.data_vencimento.strftime('%Y-%m-%d') if p.data_vencimento else None,
                    'payment_date': p.data_pagamento.strftime('%Y-%m-%d') if p.data_pagamento else None,
                    'is_paid': p.status == 'pago',
                    'bank_slip_url': p.boleto_url or '',
                }
                for p in PagamentoLoja.objects.filter(loja=loja, financeiro=f).order_by('-data_vencimento')[:20]
            ],
        })
    return out


def _pagamentos_unificado():
    """Lista unificada de pagamentos (Asaas + Mercado Pago) no formato esperado pelo frontend."""
    from asaas_integration.models import AsaasPayment
    from asaas_integration.serializers import AsaasPaymentSerializer

    out = []
    seen_asaas_ids = set()

    # 1) AsaasPayment (pagamentos registrados localmente do Asaas)
    for p in AsaasPayment.objects.all().select_related('customer').order_by('-due_date'):
        d = AsaasPaymentSerializer(p).data
        d['provedor'] = 'asaas'
        out.append(d)
        if p.asaas_id:
            seen_asaas_ids.add(p.asaas_id)

    # 2) PagamentoLoja Asaas que não estão no AsaasPayment (pagamentos antigos)
    for pl in PagamentoLoja.objects.filter(
        provedor_boleto='asaas'
    ).exclude(
        asaas_payment_id=''
    ).select_related('loja', 'loja__owner', 'financeiro').order_by('-data_vencimento'):
        if pl.asaas_payment_id in seen_asaas_ids:
            continue
        status_map = {'pago': 'RECEIVED', 'pendente': 'PENDING', 'atrasado': 'OVERDUE', 'cancelado': 'REFUNDED'}
        is_pago = pl.status == 'pago'
        out.append({
            'id': pl.id,
            'asaas_id': pl.asaas_payment_id,
            'customer_name': pl.loja.nome,
            'customer_email': getattr(pl.loja.owner, 'email', '') if pl.loja.owner else '',
            'value': str(pl.valor),
            'status': status_map.get(pl.status, 'PENDING'),
            'status_display': pl.get_status_display(),
            'due_date': pl.data_vencimento.strftime('%Y-%m-%d') if pl.data_vencimento else None,
            'payment_date': pl.data_pagamento.strftime('%Y-%m-%d') if pl.data_pagamento else None,
            'bank_slip_url': pl.boleto_url or '',
            'pix_copy_paste': pl.pix_copy_paste or '',
            'is_paid': is_pago,
            'is_pending': pl.status == 'pendente',
            'is_overdue': pl.status == 'atrasado',
            'provedor': 'asaas',
        })

    # 3) Mercado Pago
    for f in FinanceiroLoja.objects.filter(
        provedor_boleto='mercadopago'
    ).exclude(mercadopago_payment_id='').select_related('loja'):
        data_venc = f.data_proxima_cobranca.strftime('%Y-%m-%d') if f.data_proxima_cobranca else ''
        pag = (
            PagamentoLoja.objects.filter(loja=f.loja, financeiro=f)
            .order_by('-data_vencimento')
            .first()
        )
        payment_pk = pag.id if pag else f.id
        pix_cp = (pag.pix_copy_paste if pag else '') or f.pix_copy_paste or ''
        is_pago = pag and getattr(pag, 'status', '') == 'pago'
        payment_date_str = pag.data_pagamento.strftime('%Y-%m-%d') if pag and getattr(pag, 'data_pagamento', None) else None
        out.append({
            'id': payment_pk,
            'asaas_id': f.mercadopago_payment_id,
            'customer_name': f.loja.nome,
            'customer_email': getattr(f.loja.owner, 'email', ''),
            'value': str(f.valor_mensalidade),
            'status': 'RECEIVED' if is_pago else 'PENDING',
            'status_display': 'Pago' if is_pago else 'Pendente',
            'due_date': data_venc,
            'payment_date': payment_date_str,
            'bank_slip_url': f.boleto_url or '',
            'pix_copy_paste': pix_cp,
            'is_paid': is_pago,
            'is_pending': not is_pago,
            'is_overdue': False,
            'provedor': 'mercadopago',
        })
    return out


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def financeiro_unificado(request):
    """
    Resumo financeiro unificado para superadmin: Asaas + Mercado Pago.
    Retorna stats, assinaturas e pagamentos no mesmo formato dos endpoints Asaas
    para compatibilidade com a página /superadmin/financeiro.
    """
    if not request.user.is_superuser:
        return Response({'detail': 'Apenas superadmin.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        stats = _financeiro_unificado_stats()
        assinaturas = _assinaturas_unificado()
        pagamentos = _pagamentos_unificado()
        # Mesmo formato dos 3 endpoints Asaas: stats no top level + results para listas
        data = {**stats, 'assinaturas': assinaturas, 'pagamentos': pagamentos}
        return Response(data)
    except Exception as e:
        logger.exception("financeiro_unificado: %s", e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
