"""
PDF — Repasse por consulta (atendimento + procedimentos vinculados).
"""
from datetime import date
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .comissao_relatorio_pdf import (
    _CINZA,
    _COR_PRIMARIA,
    _LARGURA_UTIL,
    _fmt_brl,
    _fmt_data_br,
    _fmt_regra_comissao,
    _logo_image,
    _make_data_table,
    _merge_timbrado_fundo,
)
from .prontuario_pdf import _resolver_cabecalho_relatorio


def _bloco_atendimento(at: dict) -> list:
    styles = getSampleStyleSheet()
    titulo = Paragraph(
        f'Atendimento — {at.get("data_atendimento", "—")} às {at.get("hora_atendimento", "—")}',
        ParagraphStyle(
            'AtTit',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Bold',
            textColor=_COR_PRIMARIA,
            spaceBefore=3 * mm,
            spaceAfter=1 * mm,
        ),
    )
    info = Paragraph(
        f'<b>Paciente:</b> {at.get("paciente_nome", "—")} &nbsp;|&nbsp; '
        f'<b>Local:</b> {at.get("local_nome", "—")} &nbsp;|&nbsp; '
        f'<b>Pagamento:</b> {at.get("forma_pagamento", "—")}',
        ParagraphStyle(
            'AtInfo',
            parent=styles['Normal'],
            fontSize=7,
            textColor=colors.HexColor('#374151'),
            spaceAfter=2 * mm,
        ),
    )

    w = _LARGURA_UTIL
    consulta_tbl = _make_data_table(
        ['Item', 'Valor', 'Regra', 'Comissão'],
        [[
            'Consulta',
            _fmt_brl(at.get('valor_consulta')),
            _fmt_regra_comissao(at.get('modo_consulta', ''), at.get('regra_consulta', '')),
            _fmt_brl(at.get('comissao_consulta')),
        ]],
        col_widths=[w * 0.40, w * 0.20, w * 0.22, w * 0.18],
        font_size=7,
    )

    flow = [titulo, info, consulta_tbl]

    procs = at.get('procedimentos') or []
    if procs:
        flow.append(Spacer(1, 1.5 * mm))
        flow.append(Paragraph(
            'Procedimentos desta consulta',
            ParagraphStyle(
                'ProcSub',
                parent=styles['Normal'],
                fontSize=8,
                fontName='Helvetica-Bold',
                textColor=_COR_PRIMARIA,
                spaceAfter=1 * mm,
            ),
        ))
        proc_tbl = _make_data_table(
            ['Procedimento', 'Valor', 'Regra', 'Comissão'],
            [
                [
                    (p.get('nome') or '')[:45],
                    _fmt_brl(p.get('valor')),
                    _fmt_regra_comissao(p.get('modo', ''), p.get('regra', '')),
                    _fmt_brl(p.get('comissao')),
                ]
                for p in procs
            ],
            footer=[
                'Subtotal procedimentos',
                _fmt_brl(at.get('valor_procedimentos')),
                '',
                _fmt_brl(at.get('comissao_procedimentos')),
            ],
            col_widths=[w * 0.40, w * 0.20, w * 0.22, w * 0.18],
            font_size=7,
        )
        flow.append(proc_tbl)

    resumo = _make_data_table(
        ['', 'Valor', 'Comissão'],
        [[
            'Total do atendimento',
            _fmt_brl(at.get('valor_atendimento')),
            _fmt_brl(at.get('comissao_atendimento')),
        ]],
        col_widths=[w * 0.62, w * 0.20, w * 0.18],
        font_size=7,
    )
    flow.extend([Spacer(1, 1.5 * mm), resumo, Spacer(1, 2 * mm)])
    return flow


def _bloco_resumo_profissional(p: dict) -> list:
    styles = getSampleStyleSheet()
    data = [
        ['Total consultas — valor', _fmt_brl(p.get('valor_consulta'))],
        ['Total consultas — comissão', _fmt_brl(p.get('comissao_consulta'))],
        ['Total procedimentos — valor', _fmt_brl(p.get('valor_procedimento'))],
        ['Total procedimentos — comissão', _fmt_brl(p.get('comissao_procedimento'))],
        ['Comissão total do profissional', _fmt_brl(p.get('comissao_total'))],
    ]
    table = Table(data, colWidths=[8.5 * cm, None])
    table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, -1), (-1, -1), _COR_PRIMARIA),
        ('BOX', (0, 0), (-1, -1), 0.4, _COR_PRIMARIA),
        ('BACKGROUND', (0, 0), (-1, -2), colors.HexColor('#fdf8f9')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    return [
        Spacer(1, 2 * mm),
        HRFlowable(width='100%', thickness=0.5, color=_COR_PRIMARIA),
        Paragraph('Resumo do profissional', ParagraphStyle(
            'ResTit',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Bold',
            textColor=_COR_PRIMARIA,
            spaceBefore=2 * mm,
            spaceAfter=2 * mm,
        )),
        table,
    ]


def gerar_pdf_repasse_consulta(
    *,
    resultado: dict,
    loja,
    data_inicio: date | None,
    data_fim: date | None,
    profissional_filtro_nome: str | None = None,
) -> BytesIO:
    loja_id = loja.id
    tipo_cab, dados_cab = _resolver_cabecalho_relatorio(loja_id)

    top_margin = 2 * cm if tipo_cab != 'timbrado' else 3.2 * cm

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
        spaceAfter=2,
    )

    elements = []

    if tipo_cab == 'logo':
        img = _logo_image(dados_cab)
        if img:
            elements.append(img)
            elements.append(Spacer(1, 2 * mm))

    elements.append(Paragraph('Relatório de Repasse por Consulta', titulo_style))
    elements.append(Paragraph(
        f'Período: {_fmt_data_br(data_inicio)} a {_fmt_data_br(data_fim)}',
        subtitulo_style,
    ))
    elements.append(Paragraph(
        'Documento para o profissional conferir cada atendimento e solicitar repasse à clínica.',
        ParagraphStyle(
            'Legenda',
            parent=styles['Normal'],
            fontSize=7,
            alignment=TA_CENTER,
            textColor=_CINZA,
            spaceAfter=3 * mm,
        ),
    ))

    if profissional_filtro_nome:
        elements.append(Paragraph(
            f'Profissional: {profissional_filtro_nome}',
            ParagraphStyle(
                'Prof',
                parent=styles['Normal'],
                fontSize=11,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER,
                spaceAfter=4 * mm,
            ),
        ))

    elements.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#e5e7eb')))
    elements.append(Spacer(1, 2 * mm))

    profissionais = resultado.get('profissionais') or []
    if not profissionais:
        elements.append(Paragraph('Nenhum atendimento pago no período.', styles['Normal']))
    else:
        for idx, p in enumerate(profissionais):
            if len(profissionais) > 1 or not profissional_filtro_nome:
                elements.append(Paragraph(
                    p.get('nome', ''),
                    ParagraphStyle(
                        'NomeProf',
                        parent=styles['Heading2'],
                        fontSize=10,
                        fontName='Helvetica-Bold',
                        textColor=_COR_PRIMARIA,
                        spaceBefore=2 * mm if idx > 0 else 0,
                        spaceAfter=2 * mm,
                    ),
                ))
            for at in p.get('atendimentos') or []:
                elements.extend(_bloco_atendimento(at))
            elements.extend(_bloco_resumo_profissional(p))

        if len(profissionais) > 1:
            totais = resultado.get('totais') or {}
            elements.extend([
                Spacer(1, 4 * mm),
                HRFlowable(width='100%', thickness=0.75, color=_COR_PRIMARIA),
                Paragraph('Totais do período', ParagraphStyle(
                    'TotGeral',
                    parent=styles['Normal'],
                    fontSize=10,
                    fontName='Helvetica-Bold',
                    textColor=_COR_PRIMARIA,
                    spaceBefore=2 * mm,
                    spaceAfter=2 * mm,
                )),
                Table(
                    [
                        ['Atendimentos', str(totais.get('total_atendimentos', 0))],
                        ['Comissão total', _fmt_brl(totais.get('comissao_total'))],
                    ],
                    colWidths=[8 * cm, None],
                ),
            ])

    doc.build(elements)
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()

    if tipo_cab == 'timbrado':
        pdf_bytes = _merge_timbrado_fundo(pdf_bytes, dados_cab)

    out = BytesIO(pdf_bytes)
    out.seek(0)
    return out
