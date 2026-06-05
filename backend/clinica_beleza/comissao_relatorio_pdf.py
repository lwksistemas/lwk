"""
PDF do relatório de comissões — Clínica da Beleza.

Cabeçalho: logo da loja ou PDF timbrado (Memed), conforme configurado.
"""
import logging
from datetime import date
from io import BytesIO

import requests
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .prontuario_pdf import _resolver_cabecalho_relatorio

logger = logging.getLogger(__name__)

CHAVE_CONSULTA = '__consulta__'
LABEL_CONSULTA = 'Consulta'
_COR_PRIMARIA = colors.HexColor('#8B3D52')
_CINZA = colors.HexColor('#6b7280')


def _fmt_brl(valor) -> str:
    v = float(valor or 0)
    return f'R$ {v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def _fmt_data_br(d: date | None) -> str:
    if not d:
        return '—'
    return d.strftime('%d/%m/%Y')


def _is_linha_consulta(d: dict) -> bool:
    return d.get('tipo_linha') == 'consulta' or d.get('procedimento_nome') == LABEL_CONSULTA


def _merge_timbrado_fundo(content_pdf: bytes, timbrado_pdf: bytes) -> bytes:
    """Coloca o conteúdo sobre o PDF timbrado (fundo)."""
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        logger.warning('pypdf não instalado; PDF sem fundo timbrado.')
        return content_pdf

    try:
        reader_t = PdfReader(BytesIO(timbrado_pdf))
        reader_c = PdfReader(BytesIO(content_pdf))
        if not reader_t.pages or not reader_c.pages:
            return content_pdf
        timbrado_page = reader_t.pages[0]
        writer = PdfWriter()
        for page in reader_c.pages:
            bg = timbrado_page
            bg.merge_page(page)
            writer.add_page(bg)
        out = BytesIO()
        writer.write(out)
        out.seek(0)
        return out.getvalue()
    except Exception as e:
        logger.warning('Falha ao mesclar timbrado no PDF de comissões: %s', e)
        return content_pdf


def _logo_image(logo_url: str, max_w=5 * cm, max_h=2.5 * cm):
    try:
        resp = requests.get(logo_url, timeout=8)
        if resp.status_code != 200:
            return None
        buf = BytesIO(resp.content)
        from PIL import Image as PILImage
        pil = PILImage.open(buf)
        iw, ih = pil.size
        aspect = ih / float(iw)
        width = min(max_w, iw)
        height = width * aspect
        if height > max_h:
            height = max_h
            width = height / aspect
        buf.seek(0)
        img = Image(buf, width=width, height=height)
        img.hAlign = 'CENTER'
        return img
    except Exception as e:
        logger.warning('Logo no PDF de comissões: %s', e)
        return None


def _tabela_mini(titulo: str, headers: list, rows: list, footer: list | None = None) -> list:
    """Monta bloco título + tabela compacta."""
    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        'SubTit',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold',
        textColor=_COR_PRIMARIA,
        spaceBefore=4 * mm,
        spaceAfter=2 * mm,
    )
    flow = [Paragraph(titulo, titulo_style)]
    data = [headers] + rows
    if footer:
        data.append(footer)
    col_count = len(headers)
    col_w = [None] + [2.2 * cm] * (col_count - 1) if col_count > 1 else [None]
    table = Table(data, colWidths=col_w, repeatRows=1)
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#e5e7eb')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]
    if footer:
        fr = len(data) - 1
        style_cmds.append(('FONTNAME', (0, fr), (-1, fr), 'Helvetica-Bold'))
        style_cmds.append(('BACKGROUND', (0, fr), (-1, fr), colors.HexColor('#fafafa')))
    table.setStyle(TableStyle(style_cmds))
    flow.append(table)
    return flow


def gerar_pdf_comissoes(
    *,
    resultado: dict,
    loja,
    data_inicio: date | None,
    data_fim: date | None,
    profissional_filtro_nome: str | None = None,
) -> BytesIO:
    """
    Gera PDF do relatório de comissões.
    resultado: retorno de calcular_comissoes (dict com profissionais e totais).
    """
    loja_id = loja.id
    tipo_cab, dados_cab = _resolver_cabecalho_relatorio(loja_id)

    top_margin = 2.2 * cm
    if tipo_cab == 'timbrado':
        top_margin = 3.8 * cm

    buffer = BytesIO()
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=top_margin,
        bottomMargin=1.8 * cm,
    )

    titulo_style = ParagraphStyle(
        'Titulo',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=_COR_PRIMARIA,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    subtitulo_style = ParagraphStyle(
        'Sub',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=_CINZA,
        spaceAfter=2,
    )
    prof_style = ParagraphStyle(
        'Prof',
        parent=styles['Normal'],
        fontSize=12,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        textColor=colors.HexColor('#111827'),
        spaceAfter=6,
    )

    elements = []

    if tipo_cab == 'logo':
        img = _logo_image(dados_cab)
        if img:
            elements.append(img)
            elements.append(Spacer(1, 3 * mm))
    elif tipo_cab == 'texto' and dados_cab:
        elements.append(Paragraph(getattr(dados_cab, 'nome', '') or 'Clínica', titulo_style))
        elements.append(Spacer(1, 2 * mm))

    elements.append(Paragraph('Relatório de Comissões', titulo_style))
    periodo = f'Período: {_fmt_data_br(data_inicio)} a {_fmt_data_br(data_fim)}'
    elements.append(Paragraph(periodo, subtitulo_style))

    if profissional_filtro_nome:
        elements.append(Paragraph(f'Profissional: {profissional_filtro_nome}', prof_style))
    else:
        elements.append(Paragraph('Profissionais: todos', subtitulo_style))

    elements.append(Spacer(1, 4 * mm))
    elements.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#e5e7eb')))
    elements.append(Spacer(1, 4 * mm))

    profissionais = resultado.get('profissionais') or []
    if not profissionais:
        elements.append(Paragraph('Nenhum dado encontrado no período.', styles['Normal']))
    else:
        for idx, p in enumerate(profissionais):
            if idx > 0:
                elements.append(Spacer(1, 6 * mm))
            nome = p.get('nome', '')
            elements.append(Paragraph(nome, ParagraphStyle(
                'NomeProf',
                parent=styles['Heading2'],
                fontSize=11,
                textColor=_COR_PRIMARIA,
                spaceBefore=2 * mm,
                spaceAfter=2 * mm,
            )))

            detalhes = p.get('detalhes') or []
            linhas_c = [d for d in detalhes if _is_linha_consulta(d)]
            linhas_p = [d for d in detalhes if not _is_linha_consulta(d)]
            qtd_proc = sum(d.get('qtd', 0) for d in linhas_p)

            info = (
                f'{p.get("total_atendimentos", 0)} consulta(s) paga(s)'
                + (f' · {qtd_proc} procedimento(s)' if qtd_proc else '')
            )
            elements.append(Paragraph(info, subtitulo_style))

            regra_c = p.get('comissao_consulta_regra') or {}
            if regra_c.get('regra'):
                elements.append(Paragraph(
                    f'Regra consulta: {regra_c.get("regra", "")}',
                    subtitulo_style,
                ))

            elements.extend(_tabela_mini(
                'Consultas',
                ['Local', 'Qtd', 'Valor consulta', 'Comissão consulta'],
                [
                    [
                        d.get('local_nome') or '—',
                        str(d.get('qtd', 0)),
                        _fmt_brl(d.get('valor_consulta')),
                        _fmt_brl(d.get('comissao_consulta')),
                    ]
                    for d in linhas_c
                ],
                footer=[
                    'Subtotal',
                    str(p.get('total_atendimentos', 0)),
                    _fmt_brl(p.get('valor_consulta')),
                    _fmt_brl(p.get('comissao_consulta')),
                ] if linhas_c else None,
            ))

            elements.extend(_tabela_mini(
                'Procedimentos',
                ['Procedimento', 'Qtd', 'Valor proced.', 'Regra', 'Comissão proced.'],
                [
                    [
                        d.get('procedimento_nome', ''),
                        str(d.get('qtd', 0)),
                        _fmt_brl(d.get('valor_procedimento')),
                        d.get('regra_procedimento') or '—',
                        _fmt_brl(d.get('comissao_procedimento')),
                    ]
                    for d in linhas_p
                ],
                footer=[
                    'Subtotal',
                    str(qtd_proc),
                    _fmt_brl(p.get('valor_procedimento')),
                    '',
                    _fmt_brl(p.get('comissao_procedimento')),
                ] if linhas_p else None,
            ))

            resumo_data = [
                ['Valor consulta', _fmt_brl(p.get('valor_consulta'))],
                ['Comissão consulta', _fmt_brl(p.get('comissao_consulta'))],
                ['Valor procedimentos', _fmt_brl(p.get('valor_procedimento'))],
                ['Comissão procedimentos', _fmt_brl(p.get('comissao_procedimento'))],
                ['Comissão total', _fmt_brl(p.get('comissao_total'))],
                ['Valor total', _fmt_brl(p.get('valor_total'))],
            ]
            resumo_table = Table(resumo_data, colWidths=[5 * cm, None])
            resumo_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0, -2), (0, -1), _COR_PRIMARIA),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            elements.append(Spacer(1, 3 * mm))
            elements.append(resumo_table)

    totais = resultado.get('totais') or {}
    elements.append(Spacer(1, 8 * mm))
    elements.append(HRFlowable(width='100%', thickness=1, color=_COR_PRIMARIA))
    elements.append(Spacer(1, 3 * mm))
    elements.append(Paragraph('Totais do período', ParagraphStyle(
        'TotTit',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=_COR_PRIMARIA,
    )))

    totais_rows = [
        ['Consultas pagas', str(totais.get('total_atendimentos', 0))],
        ['Valor consulta', _fmt_brl(totais.get('valor_consulta'))],
        ['Comissão consulta', _fmt_brl(totais.get('comissao_consulta'))],
        ['Valor procedimentos', _fmt_brl(totais.get('valor_procedimento'))],
        ['Comissão procedimentos', _fmt_brl(totais.get('comissao_procedimento'))],
        ['Comissão total', _fmt_brl(totais.get('comissao_total'))],
        ['Valor total', _fmt_brl(totais.get('valor_total'))],
    ]
    tt = Table(totais_rows, colWidths=[5.5 * cm, None])
    tt.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('TEXTCOLOR', (0, -1), (-1, -1), _COR_PRIMARIA),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(tt)

    doc.build(elements)
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()

    if tipo_cab == 'timbrado':
        pdf_bytes = _merge_timbrado_fundo(pdf_bytes, dados_cab)

    out = BytesIO(pdf_bytes)
    out.seek(0)
    return out
