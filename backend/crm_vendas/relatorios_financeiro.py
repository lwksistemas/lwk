"""Relatório PDF do financeiro CRM por vendedor e grupo."""
from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from io import BytesIO

from django.db.models import Sum
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import Vendedor
from .models.financeiro import LancamentoFinanceiroCRM
from .relatorios import _criar_cabecalho_relatorio, _obter_logo_loja, calcular_periodo

logger = logging.getLogger(__name__)


def _fmt_brl(valor) -> str:
    return f'R$ {float(valor or 0):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def _resolver_periodo(periodo: str, data_inicio=None, data_fim=None):
    if periodo == 'personalizado' and data_inicio and data_fim:
        if isinstance(data_inicio, str):
            data_inicio = date.fromisoformat(data_inicio[:10])
        if isinstance(data_fim, str):
            data_fim = date.fromisoformat(data_fim[:10])
        return data_inicio, data_fim
    return calcular_periodo(periodo or 'mes_atual')


def gerar_relatorio_financeiro_vendedor(
    loja_id: int,
    *,
    periodo: str = 'mes_atual',
    vendedor_id: int | None = None,
    grupo_id: int | None = None,
    data_inicio=None,
    data_fim=None,
) -> BytesIO:
    """PDF com resumo, totais por grupo e detalhamento de lançamentos."""
    inicio, fim = _resolver_periodo(periodo, data_inicio, data_fim)

    qs = (
        LancamentoFinanceiroCRM.objects.filter(loja_id=loja_id)
        .exclude(status=LancamentoFinanceiroCRM.STATUS_CANCELADO)
        .filter(data_vencimento__gte=inicio, data_vencimento__lte=fim)
        .select_related('vendedor', 'grupo')
        .order_by('tipo', 'grupo__nome', '-data_vencimento')
    )
    if vendedor_id:
        qs = qs.filter(vendedor_id=vendedor_id)
    if grupo_id:
        qs = qs.filter(grupo_id=grupo_id)

    vendedor_nome = 'Todos os vendedores'
    if vendedor_id:
        v = Vendedor.objects.filter(id=vendedor_id).first()
        vendedor_nome = v.nome if v else f'Vendedor #{vendedor_id}'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5 * cm, leftMargin=1.5 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    normal = styles['Normal']
    subtitle = ParagraphStyle('Sub', parent=normal, fontSize=10, textColor=colors.grey)

    elements = []
    logo = _obter_logo_loja(loja_id)
    titulo = 'Relatório Financeiro — CRM Vendas'
    elements.append(_criar_cabecalho_relatorio(logo, titulo))
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(Paragraph(f'<b>Período:</b> {inicio.strftime("%d/%m/%Y")} a {fim.strftime("%d/%m/%Y")}', normal))
    elements.append(Paragraph(f'<b>Vendedor:</b> {vendedor_nome}', normal))
    elements.append(Spacer(1, 0.5 * cm))

    receitas = qs.filter(tipo=LancamentoFinanceiroCRM.TIPO_RECEITA)
    despesas = qs.filter(tipo=LancamentoFinanceiroCRM.TIPO_DESPESA)

    def totais(q):
        pagos = q.filter(status=LancamentoFinanceiroCRM.STATUS_PAGO).aggregate(t=Sum('valor'))['t'] or Decimal('0')
        pendentes = q.filter(status=LancamentoFinanceiroCRM.STATUS_PENDENTE).aggregate(t=Sum('valor'))['t'] or Decimal('0')
        return pagos, pendentes

    rec_pago, rec_pend = totais(receitas)
    desp_pago, desp_pend = totais(despesas)
    saldo = rec_pago - desp_pago

    from .models import Oportunidade
    from .relatorios import _filtro_datas_fechamento_ganho

    opp_comissao_qs = Oportunidade.objects.filter(loja_id=loja_id, etapa='closed_won').filter(
        _filtro_datas_fechamento_ganho(inicio, fim),
    )
    if vendedor_id:
        opp_comissao_qs = opp_comissao_qs.filter(vendedor_id=vendedor_id)
    total_comissao = opp_comissao_qs.aggregate(t=Sum('valor_comissao'))['t'] or Decimal('0')

    resumo_data = [
        ['Receitas pagas', _fmt_brl(rec_pago), 'Receitas pendentes', _fmt_brl(rec_pend)],
        ['Despesas pagas', _fmt_brl(desp_pago), 'Despesas pendentes', _fmt_brl(desp_pend)],
        ['Comissão de vendas', _fmt_brl(total_comissao), 'Saldo realizado', _fmt_brl(saldo)],
    ]
    resumo_table = Table(resumo_data, colWidths=[4 * cm, 3.5 * cm, 4 * cm, 3.5 * cm])
    resumo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f4fc')),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('FONTNAME', (0, 2), (0, 2), 'Helvetica-Bold'),
    ]))
    elements.append(resumo_table)
    elements.append(Spacer(1, 0.6 * cm))

    def tabela_por_grupo(tipo_label: str, tipo_val: str, cor_header):
        elements.append(Paragraph(f'<b>{tipo_label} por grupo</b>', normal))
        elements.append(Spacer(1, 0.2 * cm))
        por_grupo = (
            qs.filter(tipo=tipo_val)
            .values('grupo__nome')
            .annotate(total=Sum('valor'))
            .order_by('-total')
        )
        rows = [['Grupo', 'Total']]
        for row in por_grupo:
            rows.append([row['grupo__nome'] or 'Sem grupo', _fmt_brl(row['total'])])
        if len(rows) == 1:
            rows.append(['—', _fmt_brl(0)])
        tbl = Table(rows, colWidths=[12 * cm, 4 * cm])
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), cor_header),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        elements.append(tbl)
        elements.append(Spacer(1, 0.5 * cm))

    tabela_por_grupo('Receitas', LancamentoFinanceiroCRM.TIPO_RECEITA, colors.HexColor('#2e7d32'))
    tabela_por_grupo('Despesas', LancamentoFinanceiroCRM.TIPO_DESPESA, colors.HexColor('#c62828'))

    elements.append(Paragraph('<b>Detalhamento</b>', normal))
    elements.append(Spacer(1, 0.2 * cm))
    detalhe_rows = [['Venc.', 'Vendedor', 'Tipo', 'Grupo', 'Descrição', 'Valor', 'Status']]
    for item in qs[:200]:
        detalhe_rows.append([
            item.data_vencimento.strftime('%d/%m/%Y'),
            (item.vendedor.nome or '')[:18],
            item.get_tipo_display(),
            (item.grupo.nome if item.grupo else '—')[:14],
            item.descricao[:28],
            _fmt_brl(item.valor),
            item.get_status_display(),
        ])
    if len(detalhe_rows) == 1:
        detalhe_rows.append(['—', '—', '—', '—', 'Nenhum lançamento no período', '—', '—'])

    detalhe_table = Table(
        detalhe_rows,
        colWidths=[1.8 * cm, 2.5 * cm, 1.6 * cm, 2.2 * cm, 4.5 * cm, 2.2 * cm, 1.8 * cm],
        repeatRows=1,
    )
    detalhe_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0176d3')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(detalhe_table)

    if qs.count() > 200:
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph('(Exibindo os primeiros 200 lançamentos do período)', subtitle))

    doc.build(elements)
    buffer.seek(0)
    return buffer
