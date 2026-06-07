"""
PDF do relatório de comissões — Clínica da Beleza.

Cabeçalho: PDF timbrado (Memed), logo da loja ou texto, conforme configurado.
"""
import logging
from datetime import date
from io import BytesIO

import requests
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
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

from .prontuario_pdf import _resolver_cabecalho

logger = logging.getLogger(__name__)

LABEL_CONSULTA = 'Consulta'
_COR_PRIMARIA = colors.HexColor('#8B3D52')
_CINZA = colors.HexColor('#6b7280')
_LARGURA_UTIL = 18.4 * cm  # A4 menos margens 1.8 + 1.8


def _fmt_brl(valor) -> str:
    v = float(valor or 0)
    return f'R$ {v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def _fmt_data_br(d: date | None) -> str:
    if not d:
        return '—'
    return d.strftime('%d/%m/%Y')


def _is_linha_consulta(d: dict) -> bool:
    return d.get('tipo_linha') == 'consulta' or d.get('procedimento_nome') == LABEL_CONSULTA


def _codigo_pagamento_pdf(forma: str) -> str:
    """Código curto para caber na coluna Pag. do PDF."""
    f = (forma or '').strip().lower()
    if not f or f == '—':
        return '—'
    if f == 'pix':
        return 'PIX'
    if 'dinheiro' in f:
        return 'DIN'
    if 'crédito' in f or 'credito' in f:
        return 'CC'
    if 'débito' in f or 'debito' in f:
        return 'CD'
    if 'transfer' in f:
        return 'TRF'
    if 'cartão' in f or 'cartao' in f:
        return 'CAR'
    return (forma or '—')[:4].upper()


def _fmt_regra_comissao(modo: str, regra: str) -> str:
    """Ex.: R$ 188,00 (fixo) ou 30,00% (%)"""
    if not regra:
        return '—'
    if modo == 'fixo':
        return f'{regra} (fixo)'
    if modo == 'percentual':
        return f'{regra} (%)'
    return regra


def _merge_timbrado_fundo(content_pdf: bytes, timbrado_pdf: bytes) -> bytes:
    """Coloca o timbrado atrás de cada página de conteúdo (sem duplicar folhas)."""
    try:
        from pypdf import PdfReader, PdfWriter, Transformation
    except ImportError:
        logger.warning('pypdf não instalado; PDF sem fundo timbrado.')
        return content_pdf

    try:
        reader_c = PdfReader(BytesIO(content_pdf))
        if not reader_c.pages:
            return content_pdf

        reader_t = PdfReader(BytesIO(timbrado_pdf))
        if not reader_t.pages:
            return content_pdf

        writer = PdfWriter()
        writer.append(reader_c)

        for i in range(len(writer.pages)):
            timbrado = PdfReader(BytesIO(timbrado_pdf)).pages[0]
            writer.pages[i].merge_transformed_page(
                timbrado,
                Transformation(),
                over=False,
            )

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


def _bloco_consultas_pdf(linhas_c: list, p: dict) -> list:
    """Tabela de consultas em largura total."""
    if not linhas_c:
        return []
    w = _LARGURA_UTIL
    tabela = _make_data_table(
        ['Local', 'Pag.', 'Qtd', 'Valor consulta', 'Regra', 'Comissão consulta'],
        [
            [
                (d.get('local_nome') or '—')[:32],
                _codigo_pagamento_pdf(d.get('forma_pagamento', '')),
                str(d.get('qtd', 0)),
                _fmt_brl(d.get('valor_consulta')),
                _fmt_regra_comissao(d.get('modo_consulta', ''), d.get('regra_consulta', '')),
                _fmt_brl(d.get('comissao_consulta')),
            ]
            for d in linhas_c
        ],
        footer=[
            'Total consultas',
            '',
            str(p.get('total_atendimentos', 0)),
            _fmt_brl(p.get('valor_consulta')),
            '',
            _fmt_brl(p.get('comissao_consulta')),
        ],
        col_widths=[
            w * 0.28, w * 0.07, w * 0.07, w * 0.14, w * 0.26, w * 0.18,
        ],
        font_size=7,
    )
    return [_titulo_secao('Consultas'), tabela, _legenda_pagamento_pdf()]


def _bloco_procedimentos_pdf(linhas_p: list, p: dict, qtd_proc: int) -> list:
    """Tabela de procedimentos em largura total."""
    if not linhas_p:
        return []
    w = _LARGURA_UTIL
    tabela = _make_data_table(
        ['Procedimento', 'Convênio', 'Qtd', 'Valor', 'Regra', 'Comissão'],
        [
            [
                (d.get('procedimento_nome', '') or '')[:32],
                (d.get('convenio_nome', '') or '—')[:18],
                str(d.get('qtd', 0)),
                _fmt_brl(d.get('valor_procedimento')),
                _fmt_regra_comissao(d.get('modo_procedimento', ''), d.get('regra_procedimento', '')),
                _fmt_brl(d.get('comissao_procedimento')),
            ]
            for d in linhas_p
        ],
        footer=[
            'Total procedimentos',
            '',
            str(qtd_proc),
            _fmt_brl(p.get('valor_procedimento')),
            '',
            _fmt_brl(p.get('comissao_procedimento')),
        ],
        col_widths=[
            w * 0.28, w * 0.14, w * 0.07, w * 0.14, w * 0.20, w * 0.17,
        ],
        font_size=7,
    )
    return [_titulo_secao('Procedimentos'), tabela]


def _bloco_resumo_profissional(p: dict) -> list:
    """Resumo do profissional após consultas e procedimentos."""
    titulo_style = ParagraphStyle(
        'ResProf',
        parent=getSampleStyleSheet()['Normal'],
        fontSize=9,
        fontName='Helvetica-Bold',
        textColor=_COR_PRIMARIA,
        spaceBefore=3 * mm,
        spaceAfter=2 * mm,
    )
    data = [
        ['Total consultas — valor', _fmt_brl(p.get('valor_consulta'))],
        ['Total consultas — comissão', _fmt_brl(p.get('comissao_consulta'))],
        ['Total procedimentos — valor', _fmt_brl(p.get('valor_procedimento'))],
        ['Total procedimentos — comissão', _fmt_brl(p.get('comissao_procedimento'))],
        ['Comissão total', _fmt_brl(p.get('comissao_total'))],
        ['Valor total geral', _fmt_brl(p.get('valor_total'))],
    ]
    table = Table(data, colWidths=[8.5 * cm, None])
    table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, -2), (-1, -1), _COR_PRIMARIA),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('BOX', (0, 0), (-1, -1), 0.4, colors.HexColor('#e5e7eb')),
        ('BACKGROUND', (0, 0), (-1, -3), colors.HexColor('#fafafa')),
        ('LINEABOVE', (0, -2), (-1, -2), 0.5, _COR_PRIMARIA),
    ]))
    return [
        Spacer(1, 2 * mm),
        Paragraph('Resumo', titulo_style),
        table,
    ]


def _bloco_totais_final(styles, totais: dict, multi_prof: bool) -> list:
    """Totais de consultas e procedimentos fixos ao final do relatório."""
    titulo = 'Totais do período' if multi_prof else 'Totais'
    titulo_style = ParagraphStyle(
        'TotTit',
        parent=styles['Heading2'],
        fontSize=10,
        fontName='Helvetica-Bold',
        textColor=_COR_PRIMARIA,
        spaceBefore=4 * mm,
        spaceAfter=2 * mm,
    )
    data = [
        ['Valor total consultas', _fmt_brl(totais.get('valor_consulta'))],
        ['Comissão total consultas', _fmt_brl(totais.get('comissao_consulta'))],
        ['Valor total procedimentos', _fmt_brl(totais.get('valor_procedimento'))],
        ['Comissão total procedimentos', _fmt_brl(totais.get('comissao_procedimento'))],
        ['Comissão total', _fmt_brl(totais.get('comissao_total'))],
        ['Valor total geral', _fmt_brl(totais.get('valor_total'))],
    ]
    table = Table(data, colWidths=[8 * cm, None])
    table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 10),
        ('TEXTCOLOR', (0, -2), (-1, -1), _COR_PRIMARIA),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('BOX', (0, 0), (-1, -1), 0.5, _COR_PRIMARIA),
        ('BACKGROUND', (0, 0), (-1, -3), colors.HexColor('#fdf8f9')),
        ('LINEABOVE', (0, -2), (-1, -2), 0.75, _COR_PRIMARIA),
    ]))
    return [
        Spacer(1, 3 * mm),
        HRFlowable(width='100%', thickness=0.75, color=_COR_PRIMARIA),
        Spacer(1, 2 * mm),
        Paragraph(titulo, titulo_style),
        table,
    ]


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
    tipo_cab, dados_cab = _resolver_cabecalho(loja_id)

    top_margin = 2 * cm
    if tipo_cab == 'timbrado':
        top_margin = 3.2 * cm

    buffer = BytesIO()
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=top_margin,
        bottomMargin=1.5 * cm,
    )

    titulo_style = ParagraphStyle(
        'Titulo',
        parent=styles['Heading1'],
        fontSize=13,
        textColor=_COR_PRIMARIA,
        alignment=TA_CENTER,
        spaceAfter=3,
    )
    subtitulo_style = ParagraphStyle(
        'Sub',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=_CINZA,
        spaceAfter=1,
    )
    prof_style = ParagraphStyle(
        'Prof',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        textColor=colors.HexColor('#111827'),
        spaceAfter=4,
    )

    elements = []

    if tipo_cab == 'logo':
        img = _logo_image(dados_cab)
        if img:
            elements.append(img)
            elements.append(Spacer(1, 2 * mm))
    elif tipo_cab == 'texto' and dados_cab:
        elements.append(Paragraph(getattr(dados_cab, 'nome', '') or 'Clínica', titulo_style))
        elements.append(Spacer(1, 1 * mm))

    elements.append(Paragraph('Relatório de Comissões', titulo_style))
    periodo = f'Período: {_fmt_data_br(data_inicio)} a {_fmt_data_br(data_fim)}'
    elements.append(Paragraph(periodo, subtitulo_style))

    if profissional_filtro_nome:
        elements.append(Paragraph(f'Profissional: {profissional_filtro_nome}', prof_style))
    else:
        elements.append(Paragraph('Profissionais: todos', subtitulo_style))

    elements.append(Spacer(1, 2 * mm))
    elements.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#e5e7eb')))
    elements.append(Spacer(1, 2 * mm))

    profissionais = resultado.get('profissionais') or []
    if not profissionais:
        elements.append(Paragraph('Nenhum dado encontrado no período.', styles['Normal']))
    else:
        for idx, p in enumerate(profissionais):
            if idx > 0:
                elements.append(Spacer(1, 4 * mm))
            if len(profissionais) > 1 or not profissional_filtro_nome:
                elements.append(Paragraph(p.get('nome', ''), ParagraphStyle(
                    'NomeProf',
                    parent=styles['Heading2'],
                    fontSize=10,
                    fontName='Helvetica-Bold',
                    textColor=_COR_PRIMARIA,
                    spaceBefore=2 * mm if idx > 0 else 0,
                    spaceAfter=1 * mm,
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
            elements.extend(_bloco_consultas_pdf(linhas_c, p))
            elements.extend(_bloco_procedimentos_pdf(linhas_p, p, qtd_proc))
            elements.extend(_bloco_resumo_profissional(p))

        if len(profissionais) > 1:
            totais = resultado.get('totais') or {}
            elements.extend(_bloco_totais_final(styles, totais, multi_prof=True))

    doc.build(elements)
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()

    if tipo_cab == 'timbrado':
        pdf_bytes = _merge_timbrado_fundo(pdf_bytes, dados_cab)

    out = BytesIO(pdf_bytes)
    out.seek(0)
    return out
