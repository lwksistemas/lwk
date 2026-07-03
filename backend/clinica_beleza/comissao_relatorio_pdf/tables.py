from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import Paragraph, Table, TableStyle

from .constants import _CINZA, _COR_PRIMARIA


def _make_data_table(
    headers: list,
    rows: list,
    footer: list | None = None,
    col_widths: list | None = None,
    font_size: int = 7,
) -> Table:
    data = [headers] + rows
    if footer:
        data.append(footer)
    col_count = len(headers)
    if col_widths is None:
        col_w = [None] + [2 * cm] * (col_count - 1) if col_count > 1 else [None]
    else:
        col_w = col_widths
    table = Table(data, colWidths=col_w, repeatRows=1)
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), font_size),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#e5e7eb')),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]
    if footer:
        fr = len(data) - 1
        style_cmds.append(('FONTNAME', (0, fr), (-1, fr), 'Helvetica-Bold'))
        style_cmds.append(('BACKGROUND', (0, fr), (-1, fr), colors.HexColor('#fafafa')))
    table.setStyle(TableStyle(style_cmds))
    return table


def _legenda_pagamento_pdf() -> Paragraph:
    styles = getSampleStyleSheet()
    return Paragraph(
        'Pag.: PIX · DIN (dinheiro) · CC (crédito) · CD (débito) · TRF (transferência)',
        ParagraphStyle(
            'LegPag',
            parent=styles['Normal'],
            fontSize=5,
            textColor=_CINZA,
            spaceBefore=0,
            spaceAfter=1 * mm,
        ),
    )


def _titulo_secao(texto: str) -> Paragraph:
    styles = getSampleStyleSheet()
    return Paragraph(texto, ParagraphStyle(
        'SecTit',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica-Bold',
        textColor=_COR_PRIMARIA,
        spaceBefore=2 * mm,
        spaceAfter=1 * mm,
    ))
