"""
Geração de PDF do Relatório de Comissão com área de assinatura.
"""
from io import BytesIO
from decimal import Decimal
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
import logging

logger = logging.getLogger(__name__)

_AZUL = colors.HexColor('#0176d3')
_CINZA = colors.HexColor('#f3f4f6')
_CINZA_ESCURO = colors.HexColor('#6b7280')
_VERDE = colors.HexColor('#059669')
_VERMELHO = colors.HexColor('#dc2626')


def _fmt_brl(valor) -> str:
    v = float(valor or 0)
    return f'R$ {v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def _fmt_data(d) -> str:
    if not d:
        return '—'
    if hasattr(d, 'strftime'):
        # Se tem hora (datetime), mostrar data + hora
        if hasattr(d, 'hour'):
            return d.strftime('%d/%m/%Y %H:%M')
        return d.strftime('%d/%m/%Y')
    return str(d)


def gerar_pdf_relatorio_comissao(relatorio, loja, incluir_assinaturas: bool = False) -> BytesIO:
    """
    Gera PDF do relatório de comissão.

    Args:
        relatorio: instância de RelatorioComissao
        loja: instância de Loja (prestador)
        incluir_assinaturas: se True, inclui bloco com dados das assinaturas já realizadas
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )
    elements = []
    styles = getSampleStyleSheet()

    # ── Estilos ──────────────────────────────────────────────────────────────
    titulo_style = ParagraphStyle(
        'RCTitulo',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=_AZUL,
        alignment=TA_CENTER,
        spaceBefore=0,
        spaceAfter=6,
    )
    subtitulo_style = ParagraphStyle(
        'RCSubtitulo',
        parent=styles['Normal'],
        fontSize=10,
        textColor=_CINZA_ESCURO,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    secao_style = ParagraphStyle(
        'RCSecao',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=_AZUL,
        spaceBefore=12,
        spaceAfter=4,
    )
    info_style = ParagraphStyle(
        'RCInfo',
        parent=styles['Normal'],
        fontSize=9,
        spaceBefore=0,
        spaceAfter=2,
        leading=13,
    )
    rodape_style = ParagraphStyle(
        'RCRodape',
        parent=styles['Normal'],
        fontSize=7,
        textColor=_CINZA_ESCURO,
        alignment=TA_CENTER,
    )
    assin_label_style = ParagraphStyle(
        'RCAssinLabel',
        parent=styles['Normal'],
        fontSize=8,
        textColor=_CINZA_ESCURO,
        alignment=TA_CENTER,
    )
    assin_nome_style = ParagraphStyle(
        'RCAssinNome',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        spaceBefore=2,
    )

    # ── Cabeçalho ────────────────────────────────────────────────────────────
    elements.append(Paragraph('RELATÓRIO DE COMISSÃO', titulo_style))
    elements.append(Paragraph(relatorio.titulo or relatorio.numero, subtitulo_style))
    elements.append(Paragraph(
        f'Período: {_fmt_data(relatorio.periodo_inicio)} a {_fmt_data(relatorio.periodo_fim)}',
        subtitulo_style,
    ))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(HRFlowable(width='100%', thickness=1, color=_AZUL))
    elements.append(Spacer(1, 0.3 * cm))

    # ── Dados do Prestador + Empresa Contratante (lado a lado em cards) ──────
    card_style = ParagraphStyle(
        'RCCard',
        parent=styles['Normal'],
        fontSize=8.5,
        spaceBefore=0,
        spaceAfter=1,
        leading=12,
    )
    card_email_style = ParagraphStyle(
        'RCCardEmail',
        parent=styles['Normal'],
        fontSize=7.5,
        spaceBefore=0,
        spaceAfter=1,
        leading=11,
    )
    card_title_style = ParagraphStyle(
        'RCCardTitle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=_AZUL,
        spaceBefore=0,
        spaceAfter=3,
        leading=12,
    )

    # Prestador de Serviços
    prestador_lines = [Paragraph('<b>Prestador de Serviços</b>', card_title_style)]
    prestador_lines.append(Paragraph(f'{loja.nome or "—"}', card_style))
    if getattr(loja, 'cpf_cnpj', ''):
        prestador_lines.append(Paragraph(f'<font color="#6b7280">CNPJ:</font> {loja.cpf_cnpj}', card_style))
    # Email do prestador (via owner da loja)
    prestador_email = getattr(loja, 'owner', None) and getattr(loja.owner, 'email', '')
    if prestador_email:
        prestador_lines.append(Paragraph(f'{prestador_email}', card_email_style))

    # Empresa Contratante
    ep = relatorio.empresa_prestadora
    contratante_lines = [Paragraph('<b>Empresa Contratante</b>', card_title_style)]
    contratante_lines.append(Paragraph(f'{ep.nome or "—"}', card_style))
    if ep.cnpj:
        contratante_lines.append(Paragraph(f'<font color="#6b7280">CNPJ:</font> {ep.cnpj}', card_style))
    if ep.email:
        contratante_lines.append(Paragraph(f'{ep.email}', card_email_style))

    # Vendedor
    vendedor_lines = []
    v = relatorio.vendedor or getattr(relatorio.empresa_prestadora, 'vendedor', None)
    # Fallback: buscar Vendedor vinculado ao owner da loja
    if not v and getattr(loja, 'owner', None):
        try:
            from superadmin.models import VendedorUsuario
            from .models import Vendedor
            vu = VendedorUsuario.objects.using('default').filter(
                user=loja.owner, loja=loja
            ).first()
            if vu:
                v = Vendedor.objects.filter(id=vu.vendedor_id, loja_id=loja.id).first()
        except Exception:
            pass
    if v:
        vendedor_lines = [Paragraph('<b>Vendedor Responsável</b>', card_title_style)]
        vendedor_lines.append(Paragraph(f'{v.nome}', card_style))
        if v.email:
            vendedor_lines.append(Paragraph(f'{v.email}', card_email_style))

    # Montar tabela com 3 colunas (cards lado a lado)
    card_table_data = [[prestador_lines, contratante_lines, vendedor_lines]]
    card_table = Table(card_table_data, colWidths=[5.5 * cm, 5.5 * cm, 5.5 * cm])
    card_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (0, 0), 0.5, colors.HexColor('#d1d5db')),
        ('BOX', (1, 0), (1, 0), 0.5, colors.HexColor('#d1d5db')),
        ('BOX', (2, 0), (2, 0), 0.5, colors.HexColor('#d1d5db')),
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f9fafb')),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#f9fafb')),
        ('BACKGROUND', (2, 0), (2, 0), colors.HexColor('#f9fafb')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(card_table)
    elements.append(Spacer(1, 0.4 * cm))

    # ── Resumo Financeiro ────────────────────────────────────────────────────
    elements.append(Paragraph('<b>Resumo Financeiro</b>', secao_style))
    resumo_data = [
        ['Descrição', 'Valor'],
        ['Quantidade de Vendas', str(relatorio.quantidade_vendas)],
        ['Total de Vendas', _fmt_brl(relatorio.valor_total_vendas)],
        ['Total de Comissão', _fmt_brl(relatorio.valor_total_comissao)],
    ]
    t_resumo = Table(resumo_data, colWidths=[10 * cm, 6 * cm])
    t_resumo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), _AZUL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BACKGROUND', (0, 1), (-1, -1), _CINZA),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, _CINZA]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        # Destaque na linha de comissão
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1, -1), (1, -1), _VERDE),
    ]))
    elements.append(t_resumo)
    elements.append(Spacer(1, 0.4 * cm))

    # ── Detalhamento das Vendas ──────────────────────────────────────────────
    oportunidades = relatorio.dados_oportunidades or []
    if oportunidades:
        elements.append(Paragraph('<b>Detalhamento das Vendas</b>', secao_style))
        det_data = [['Data', 'Cliente', 'Valor Venda', 'Comissão']]
        for op in oportunidades:
            det_data.append([
                op.get('data', '—'),
                (op.get('cliente', '—') or '—')[:35],
                _fmt_brl(op.get('valor', 0)),
                _fmt_brl(op.get('comissao', 0)),
            ])
        t_det = Table(det_data, colWidths=[2.5 * cm, 7 * cm, 3.5 * cm, 3 * cm])
        t_det.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, _CINZA]),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e5e7eb')),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(t_det)
        elements.append(Spacer(1, 0.4 * cm))

    # ── Assinaturas já realizadas (quando incluir_assinaturas=True) ──────────
    if incluir_assinaturas:
        elements.append(HRFlowable(width='100%', thickness=0.5, color=_CINZA_ESCURO))
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph('<b>Registro de Assinaturas Digitais</b>', secao_style))

        assin_rows = []

        # Empresa prestadora
        if relatorio.empresa_aprovado_em:
            assin_rows.append([
                'Empresa Contratante',
                relatorio.empresa_aprovado_nome or ep.nome,
                _fmt_data(relatorio.empresa_aprovado_em),
                relatorio.empresa_aprovado_ip or '—',
                'Aprovado ✓',
            ])
        elif relatorio.empresa_reprovado_em:
            assin_rows.append([
                'Empresa Contratante',
                ep.nome,
                _fmt_data(relatorio.empresa_reprovado_em),
                '—',
                'Reprovado ✗',
            ])

        # Vendedor
        if relatorio.vendedor_assinado_em:
            vendedor_assin_nome = relatorio.vendedor_assinado_nome
            # Fallback: usar nome do vendedor resolvido (v) se o nome salvo for genérico ou igual ao nome da loja
            if v and (not vendedor_assin_nome or vendedor_assin_nome == '—' or vendedor_assin_nome == loja.nome):
                vendedor_assin_nome = v.nome
            elif not vendedor_assin_nome:
                vendedor_assin_nome = '—'
            assin_rows.append([
                'Vendedor',
                vendedor_assin_nome,
                _fmt_data(relatorio.vendedor_assinado_em),
                relatorio.vendedor_assinado_ip or '—',
                'Assinado ✓',
            ])

        if assin_rows:
            t_assin = Table(
                [['Parte', 'Nome', 'Data/Hora', 'IP', 'Status']] + assin_rows,
                colWidths=[3 * cm, 5 * cm, 3 * cm, 3.5 * cm, 2.5 * cm],
            )
            t_assin.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), _AZUL),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, _CINZA]),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e5e7eb')),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            elements.append(t_assin)
        elements.append(Spacer(1, 0.4 * cm))

    # ── Área de Assinatura (quando ainda não assinado) ───────────────────────
    else:
        elements.append(Spacer(1, 0.8 * cm))
        elements.append(HRFlowable(width='100%', thickness=0.5, color=_CINZA_ESCURO))
        elements.append(Spacer(1, 0.4 * cm))
        elements.append(Paragraph('<b>Assinaturas</b>', secao_style))
        elements.append(Spacer(1, 0.3 * cm))

        linha_assin = '_' * 45
        # Nome do vendedor para assinatura
        nome_vendedor_assin = v.nome if v else 'Vendedor'

        assin_table_data = [[
            Paragraph(
                f'{linha_assin}<br/><br/>'
                f'<b>{ep.nome}</b><br/>'
                f'<font size="8" color="grey">Empresa Contratante</font>',
                assin_nome_style,
            ),
            Paragraph(
                f'{linha_assin}<br/><br/>'
                f'<b>{nome_vendedor_assin}</b><br/>'
                f'<font size="8" color="grey">Vendedor Responsável</font>',
                assin_nome_style,
            ),
        ]]
        t_assin_vazia = Table(assin_table_data, colWidths=[8 * cm, 8 * cm])
        t_assin_vazia.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(t_assin_vazia)
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(Paragraph(
            'Data: _____ / _____ / _________',
            ParagraphStyle('data', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER),
        ))

    # ── Observações ──────────────────────────────────────────────────────────
    if relatorio.observacoes:
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph('<b>Observações</b>', secao_style))
        elements.append(Paragraph(relatorio.observacoes, info_style))

    # ── Rodapé ───────────────────────────────────────────────────────────────
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(HRFlowable(width='100%', thickness=0.5, color=_CINZA_ESCURO))
    elements.append(Spacer(1, 0.2 * cm))
    from django.utils import timezone
    elements.append(Paragraph(
        f'Documento gerado em {timezone.now().strftime("%d/%m/%Y às %H:%M")} | '
        f'Nº {relatorio.numero} | LWK Sistemas',
        rodape_style,
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer
