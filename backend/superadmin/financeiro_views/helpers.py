"""Helpers compartilhados do financeiro das lojas."""
import logging
from datetime import date

from ..models import FinanceiroLoja, PagamentoLoja

logger = logging.getLogger(__name__)


def _boleto_pix_liberado_para_vencimento(due_date) -> bool:
    """Alinhado ao cron e à UI: boleto/PIX só dentro de 10 dias do vencimento."""
    from superadmin.services.assinatura_bloqueio_service import DAYS_TO_WARN_BOLETO

    if not due_date:
        return True
    if not isinstance(due_date, date):
        return True
    return (due_date - date.today()).days <= DAYS_TO_WARN_BOLETO

def _mercadopago_payment_ids_for_boleto(pagamento):
    """IDs MP únicos para tentar obter URL do boleto (linha do pagamento + financeiro)."""
    ids = []
    pid = (getattr(pagamento, 'mercadopago_payment_id', None) or '').strip()
    if pid:
        ids.append(pid)
    fin = getattr(pagamento, 'financeiro', None)
    if fin:
        fid = (getattr(fin, 'mercadopago_payment_id', None) or '').strip()
        if fid and fid not in ids:
            ids.append(fid)
    return ids


def _resolve_asaas_payment_id(pagamento):
    """
    ID do pagamento Asaas: prioriza PagamentoLoja, depois FinanceiroLoja,
    depois cobrança pendente/vencida na assinatura Asaas com mesma data de vencimento.
    """
    pid = (getattr(pagamento, 'asaas_payment_id', None) or '').strip()
    if pid:
        return pid
    fin = getattr(pagamento, 'financeiro', None)
    if fin:
        pid = (getattr(fin, 'asaas_payment_id', None) or '').strip()
        if pid:
            return pid
    try:
        from asaas_integration.models import AsaasPayment, LojaAssinatura

        ass = (
            LojaAssinatura.objects.filter(loja_slug=pagamento.loja.slug)
            .select_related('asaas_customer')
            .first()
        )
        if not ass:
            return ''
        qs = AsaasPayment.objects.filter(
            customer=ass.asaas_customer,
            status__in=['PENDING', 'OVERDUE'],
        ).order_by('-due_date')
        due = getattr(pagamento, 'data_vencimento', None)
        if due:
            m = qs.filter(due_date=due).first()
            if m and m.asaas_id:
                logger.info(
                    'baixar_boleto: asaas_id resolvido via AsaasPayment (data=%s) id=%s',
                    due,
                    m.asaas_id,
                )
                return m.asaas_id
        m = qs.first()
        if m and m.asaas_id:
            logger.info(
                'baixar_boleto: asaas_id resolvido via último PENDING/OVERDUE id=%s',
                m.asaas_id,
            )
            return m.asaas_id
    except Exception as e:
        logger.warning('baixar_boleto: fallback AsaasPayment: %s', e)
    return ''


def _nfse_para_pagamento(pagamento, asaas_id=''):
    """NFS-e vinculada ao PagamentoLoja (local, Asaas ou emissão manual da mesma loja/valor)."""
    try:
        from decimal import Decimal

        from ..models import NFSeEmitida

        nf = NFSeEmitida.objects.filter(pagamento=pagamento, status='emitida').first()
        if not nf and asaas_id:
            nf = NFSeEmitida.objects.filter(asaas_payment_id=asaas_id, status='emitida').first()
        if not nf and pagamento.loja_id:
            pl_valor = Decimal(str(pagamento.valor or 0)).quantize(Decimal('0.01'))
            candidatas = NFSeEmitida.objects.filter(
                loja_id=pagamento.loja_id,
                status='emitida',
                pagamento__isnull=True,
            ).order_by('-created_at')
            for cand in candidatas:
                cand_valor = Decimal(str(cand.valor or 0)).quantize(Decimal('0.01'))
                if cand_valor == pl_valor:
                    nf = cand
                    nf.pagamento = pagamento
                    if asaas_id and not (nf.asaas_payment_id or '').strip():
                        nf.asaas_payment_id = asaas_id
                    nf.save(update_fields=['pagamento', 'asaas_payment_id'])
                    break
        return nf
    except Exception as e:
        logger.warning('nfse para pagamento %s: %s', getattr(pagamento, 'id', '?'), e)
        return None


def _cancelar_pagamentos_loja_obsoletos(loja):
    """
    Cancela PagamentoLoja pendente/atrasado quando já existe pago na mesma
    referência ou vencimento (cobrança duplicada após confirmação de pagamento).
    """
    pagos = PagamentoLoja.objects.filter(loja=loja, status='pago')
    if not pagos.exists():
        return 0

    cancelados = 0
    pendentes = PagamentoLoja.objects.filter(loja=loja, status__in=['pendente', 'atrasado'])
    for p in pendentes:
        base = pagos.filter(valor=p.valor)
        duplicado = False
        if p.referencia_mes and base.filter(referencia_mes=p.referencia_mes).exists() or p.data_vencimento and base.filter(data_vencimento=p.data_vencimento).exists():
            duplicado = True
        if not duplicado:
            continue
        p.status = 'cancelado'
        p.observacoes = (
            (p.observacoes or '').strip()
            + '\n[auto] Cancelado: já existe pagamento confirmado para esta referência/vencimento.'
        ).strip()
        p.save(update_fields=['status', 'observacoes'])
        cancelados += 1
        logger.info(
            'PagamentoLoja %s cancelado (duplicado obsoleto) loja=%s ref=%s venc=%s',
            p.id,
            loja.slug,
            p.referencia_mes,
            p.data_vencimento,
        )
    return cancelados


def _suprimir_pendentes_obsoletos_historico(historico):
    """Remove do histórico cobranças em aberto já quitadas em outro lançamento."""
    if not historico:
        return historico

    paid_by_due = set()
    paid_by_ref = set()
    for item in historico:
        if not item.get('is_paid'):
            continue
        valor = round(float(item.get('valor') or 0), 2)
        due = item.get('data_vencimento') or ''
        if due:
            paid_by_due.add((due, valor))
        ref = item.get('referencia_mes') or ''
        if ref:
            paid_by_ref.add((ref, valor))

    result = []
    for item in historico:
        if item.get('is_pending') or item.get('is_overdue'):
            valor = round(float(item.get('valor') or 0), 2)
            due = item.get('data_vencimento') or ''
            ref = item.get('referencia_mes') or ''
            if due and (due, valor) in paid_by_due:
                continue
            if ref and (ref, valor) in paid_by_ref:
                continue
        result.append(item)
    return result


def _deduplicar_historico_pagamentos(historico):
    """Remove cobranças duplicadas (mesmo asaas_id ou mesma fatura em aberto)."""
    if not historico:
        return historico

    def item_rank(item):
        rank = 0
        if (item.get('asaas_id') or '').strip():
            rank += 8
        if (item.get('boleto_url') or '').strip():
            rank += 4
        if item.get('pagamento_loja_id'):
            rank += 2
        return rank

    ordered = sorted(historico, key=item_rank, reverse=True)
    seen_asaas = set()
    seen_open = set()
    kept_ids = set()
    result = []

    for item in ordered:
        asaas_id = (item.get('asaas_id') or '').strip()
        is_open = item.get('is_pending') or item.get('is_overdue')
        open_key = None
        if is_open:
            open_key = (
                item.get('data_vencimento') or '',
                round(float(item.get('valor') or 0), 2),
            )
        if asaas_id:
            if asaas_id in seen_asaas:
                continue
            seen_asaas.add(asaas_id)
        elif open_key:
            if open_key in seen_open:
                continue
            seen_open.add(open_key)
        pid = item.get('pagamento_loja_id') or item.get('id')
        if pid and pid in kept_ids:
            continue
        if pid:
            kept_ids.add(pid)
        result.append(item)

    result.sort(key=lambda x: x.get('data_vencimento') or '', reverse=True)
    return result


def _build_historico_pagamentos_loja(
    loja,
    financeiro,
    boleto_url_fallback='',
    pix_copy_fallback='',
    asaas_due_fallback=None,
):
    """
    Histórico unificado para o painel da loja (PagamentoLoja + dados Asaas quando existir).
    Cada item usa pagamento_loja_id para baixar boleto / NFS-e.
    """
    from asaas_integration.models import AsaasPayment, LojaAssinatura

    _cancelar_pagamentos_loja_obsoletos(loja)

    asaas_by_id = {}
    asaas_by_due = {}
    try:
        ass = LojaAssinatura.objects.filter(loja_slug=loja.slug).select_related('asaas_customer').first()
        if ass:
            for ap in AsaasPayment.objects.filter(customer=ass.asaas_customer).order_by('-due_date'):
                if ap.asaas_id:
                    asaas_by_id[ap.asaas_id] = ap
                    if ap.due_date:
                        asaas_by_due[ap.due_date] = ap
    except Exception as e:
        logger.warning('historico loja %s: AsaasPayment: %s', loja.slug, e)

    historico = []
    pls = (
        PagamentoLoja.objects.filter(loja=loja)
        .exclude(status='cancelado')
        .select_related('financeiro')
        .order_by('-data_vencimento')
    )

    for pl in pls:
        asaas_id = (pl.asaas_payment_id or '').strip()
        if not asaas_id and getattr(pl, 'financeiro', None):
            asaas_id = (pl.financeiro.asaas_payment_id or '').strip()
        ap = asaas_by_id.get(asaas_id) if asaas_id else None
        if ap is None and pl.data_vencimento:
            ap = asaas_by_due.get(pl.data_vencimento)
            if ap and ap.asaas_id:
                asaas_id = ap.asaas_id
        provedor = (getattr(pl, 'provedor_boleto', None) or getattr(financeiro, 'provedor_boleto', None) or 'asaas')

        if pl.status == 'pago':
            status_display = 'Pago'
            is_paid, is_pending, is_overdue = True, False, False
            status_raw = 'RECEIVED' if ap else 'pago'
        elif pl.status == 'atrasado':
            status_display = 'Vencido'
            is_paid, is_pending, is_overdue = False, False, True
            status_raw = 'OVERDUE' if ap else 'atrasado'
        else:
            status_display = 'Aguardando pagamento'
            is_paid, is_pending, is_overdue = False, True, False
            status_raw = 'PENDING' if ap else 'pendente'

        if ap:
            if ap.status in ['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']:
                status_display = 'Recebida'
                is_paid, is_pending, is_overdue = True, False, False
                status_raw = ap.status
            elif ap.status == 'OVERDUE':
                status_display = 'Vencida'
                is_paid, is_pending, is_overdue = False, False, True
                status_raw = ap.status
            elif ap.status == 'PENDING':
                status_raw = ap.status

        boleto_url = (pl.boleto_url or '').strip()
        if not boleto_url and ap:
            boleto_url = (ap.bank_slip_url or ap.invoice_url or '').strip()
        if not boleto_url and is_pending and boleto_url_fallback:
            pl_due = pl.data_vencimento
            if asaas_due_fallback and pl_due == asaas_due_fallback:
                boleto_url = boleto_url_fallback

        pix_copy = (pl.pix_copy_paste or '').strip()
        pix_qr = (pl.pix_qr_code or '').strip()
        if ap:
            pix_copy = pix_copy or (ap.pix_copy_paste or '').strip()
            pix_qr = pix_qr or (ap.pix_qr_code or '').strip()
        if not pix_copy and is_pending:
            pix_copy = (pix_copy_fallback or '').strip()

        if (is_pending or is_overdue) and pl.data_vencimento and not _boleto_pix_liberado_para_vencimento(
            pl.data_vencimento
        ):
            boleto_url = ''
            pix_copy = ''
            pix_qr = ''

        data_pagamento = None
        if pl.data_pagamento:
            data_pagamento = pl.data_pagamento.strftime('%Y-%m-%d')
        elif ap and ap.payment_date:
            data_pagamento = ap.payment_date.strftime('%Y-%m-%d')

        nf = _nfse_para_pagamento(pl, asaas_id)

        historico.append({
            'pagamento_loja_id': pl.id,
            'id': pl.id,
            'asaas_id': asaas_id or '',
            'mercadopago_payment_id': (pl.mercadopago_payment_id or '').strip(),
            'provedor_boleto': provedor,
            'valor': float(ap.value if ap and ap.value is not None else (pl.valor or 0)),
            'status': status_raw,
            'status_display': status_display,
            'data_vencimento': pl.data_vencimento.strftime('%Y-%m-%d') if pl.data_vencimento else None,
            'data_pagamento': data_pagamento,
            'boleto_url': boleto_url,
            'pix_copy_paste': pix_copy,
            'pix_qr_code': pix_qr,
            'is_paid': is_paid,
            'is_pending': is_pending,
            'is_overdue': is_overdue,
            'tem_nota_fiscal': bool(nf),
            'numero_nf': (nf.numero_nf or '') if nf else '',
            'nf_pdf_url': (nf.pdf_url or '') if nf else '',
            'referencia_mes': pl.referencia_mes.strftime('%Y-%m-%d') if pl.referencia_mes else None,
            'pode_baixar_boleto': (
                not is_paid
                and bool(asaas_id or boleto_url or pl.mercadopago_payment_id)
            ),
        })

    historico = _deduplicar_historico_pagamentos(historico)
    historico = _suprimir_pendentes_obsoletos_historico(historico)

    if not historico and boleto_url_fallback:
        mp_id = (getattr(financeiro, 'mercadopago_payment_id', None) or '').strip()
        historico.append({
            'pagamento_loja_id': 0,
            'id': 0,
            'asaas_id': mp_id,
            'mercadopago_payment_id': mp_id,
            'provedor_boleto': getattr(financeiro, 'provedor_boleto', 'mercadopago'),
            'valor': float(financeiro.valor_mensalidade),
            'status': 'PENDING',
            'status_display': 'Aguardando pagamento',
            'data_vencimento': financeiro.data_proxima_cobranca.strftime('%Y-%m-%d') if financeiro.data_proxima_cobranca else None,
            'data_pagamento': None,
            'boleto_url': boleto_url_fallback,
            'pix_copy_paste': pix_copy_fallback or '',
            'pix_qr_code': '',
            'is_paid': False,
            'is_pending': True,
            'is_overdue': False,
            'tem_nota_fiscal': False,
            'numero_nf': '',
            'nf_pdf_url': '',
            'referencia_mes': None,
        })

    return historico


def _get_or_create_financeiro_loja(loja):
    """Retorna FinanceiroLoja existente ou cria registro mínimo para lojas antigas sem financeiro."""
    try:
        return loja.financeiro
    except FinanceiroLoja.DoesNotExist:
        from superadmin.services import FinanceiroService

        dia = getattr(loja, 'dia_vencimento', None) or 10
        financeiro = FinanceiroService.criar_financeiro_loja(loja, dia_vencimento=dia)
        logger.warning('Financeiro auto-criado para loja %s (id=%s)', loja.slug, loja.id)
        return financeiro
