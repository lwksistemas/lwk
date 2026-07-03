"""Relatório PDF do financeiro CRM por vendedor e grupo."""
from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from io import BytesIO

from django.db.models import Sum
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import Vendedor
from .models.financeiro import GrupoFinanceiroCRM, LancamentoFinanceiroCRM
from .periodo import filtro_fechamento_no_periodo as _filtro_datas_fechamento_ganho
from .relatorios_pdf_common import _criar_cabecalho_relatorio, _obter_logo_loja

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
    from .services_financeiro import calcular_intervalo_vencimento

    return calcular_intervalo_vencimento(periodo, data_inicio, data_fim)


def gerar_relatorio_financeiro_vendedor(
    loja_id: int,
    *,
    periodo: str = 'mes_atual',
    vendedor_id: int | None = None,
    grupo_id: int | None = None,
    data_inicio=None,
    data_fim=None,
) -> BytesIO:
    """PDF com resumo e totais por grupo (sem listagem linha a linha)."""
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

    grupo_nome = 'Todos os grupos'
    grupo_obj = None
    if grupo_id:
        grupo_obj = GrupoFinanceiroCRM.objects.filter(loja_id=loja_id, id=grupo_id).first()
        grupo_nome = grupo_obj.nome if grupo_obj else f'Grupo #{grupo_id}'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5 * cm, leftMargin=1.5 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    normal = styles['Normal']

    elements = []
    logo = _obter_logo_loja(loja_id)
    titulo = 'Relatório Financeiro — CRM Vendas'
    if grupo_id:
        titulo = f'Relatório por Grupo — {grupo_nome}'
    elements.append(_criar_cabecalho_relatorio(logo, titulo))
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(Paragraph(f'<b>Período:</b> {inicio.strftime("%d/%m/%Y")} a {fim.strftime("%d/%m/%Y")}', normal))
    elements.append(Paragraph(f'<b>Vendedor:</b> {vendedor_nome}', normal))
    elements.append(Paragraph(f'<b>Grupo:</b> {grupo_nome}', normal))
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
    from .services_dashboard import calcular_intervalo_datas

    inicio_opp, fim_opp = calcular_intervalo_datas(periodo, data_inicio, data_fim)
    opp_comissao_qs = Oportunidade.objects.filter(loja_id=loja_id, etapa='closed_won').filter(
        _filtro_datas_fechamento_ganho(inicio_opp, fim_opp),
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

    if not grupo_id:
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

    if grupo_id and grupo_obj and (grupo_obj.nome or '').strip().lower() == 'comissão de vendas':
        n_opps = opp_comissao_qs.count()
        comissao_rows = [
            ['Oportunidades ganhas no período', str(n_opps)],
            ['Comissão total (oportunidades)', _fmt_brl(total_comissao)],
            ['Recebido', _fmt_brl(rec_pago)],
            ['Pendente', _fmt_brl(rec_pend)],
        ]
        comissao_table = Table(comissao_rows, colWidths=[10 * cm, 6 * cm])
        comissao_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f5e9')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        elements.append(Paragraph('<b>Comissão de vendas</b>', normal))
        elements.append(Spacer(1, 0.2 * cm))
        elements.append(comissao_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer
