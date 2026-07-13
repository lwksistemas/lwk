from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from .constants import _COR_PRIMARIA, _LARGURA_UTIL
from .formatting import _codigo_pagamento_pdf, _fmt_brl, _fmt_regra_comissao
from .tables import _legenda_pagamento_pdf, _make_data_table, _titulo_secao


def _bloco_consultas_pdf(linhas_c: list, p: dict) -> list:
    """Tabela de consultas em largura total."""
    if not linhas_c:
        return []
    w = _LARGURA_UTIL
    tabela = _make_data_table(
        ["Local", "Pag.", "Qtd", "Valor consulta", "Regra", "Comissão consulta"],
        [
            [
                (d.get("local_nome") or "—")[:32],
                _codigo_pagamento_pdf(d.get("forma_pagamento", "")),
                str(d.get("qtd", 0)),
                _fmt_brl(d.get("valor_consulta")),
                _fmt_regra_comissao(d.get("modo_consulta", ""), d.get("regra_consulta", "")),
                _fmt_brl(d.get("comissao_consulta")),
            ]
            for d in linhas_c
        ],
        footer=[
            "Total consultas",
            "",
            str(p.get("total_atendimentos", 0)),
            _fmt_brl(p.get("valor_consulta")),
            "",
            _fmt_brl(p.get("comissao_consulta")),
        ],
        col_widths=[
            w * 0.28, w * 0.07, w * 0.07, w * 0.14, w * 0.26, w * 0.18,
        ],
        font_size=7,
    )
    return [_titulo_secao("Consultas"), tabela, _legenda_pagamento_pdf()]


def _bloco_procedimentos_pdf(linhas_p: list, p: dict, qtd_proc: int) -> list:
    """Tabela de procedimentos em largura total."""
    if not linhas_p:
        return []
    w = _LARGURA_UTIL
    tabela = _make_data_table(
        ["Procedimento", "Convênio", "Qtd", "Valor", "Regra", "Comissão"],
        [
            [
                (d.get("procedimento_nome", "") or "")[:32],
                (d.get("convenio_nome", "") or "—")[:18],
                str(d.get("qtd", 0)),
                _fmt_brl(d.get("valor_procedimento")),
                _fmt_regra_comissao(d.get("modo_procedimento", ""), d.get("regra_procedimento", "")),
                _fmt_brl(d.get("comissao_procedimento")),
            ]
            for d in linhas_p
        ],
        footer=[
            "Total procedimentos",
            "",
            str(qtd_proc),
            _fmt_brl(p.get("valor_procedimento")),
            "",
            _fmt_brl(p.get("comissao_procedimento")),
        ],
        col_widths=[
            w * 0.28, w * 0.14, w * 0.07, w * 0.14, w * 0.20, w * 0.17,
        ],
        font_size=7,
    )
    return [_titulo_secao("Procedimentos"), tabela]


def _bloco_resumo_profissional(p: dict) -> list:
    """Resumo do profissional após consultas e procedimentos."""
    titulo_style = ParagraphStyle(
        "ResProf",
        parent=getSampleStyleSheet()["Normal"],
        fontSize=9,
        fontName="Helvetica-Bold",
        textColor=_COR_PRIMARIA,
        spaceBefore=3 * mm,
        spaceAfter=2 * mm,
    )
    data = [
        ["Total consultas — valor", _fmt_brl(p.get("valor_consulta"))],
        ["Total consultas — comissão", _fmt_brl(p.get("comissao_consulta"))],
        ["Total procedimentos — valor", _fmt_brl(p.get("valor_procedimento"))],
        ["Total procedimentos — comissão", _fmt_brl(p.get("comissao_procedimento"))],
        ["Comissão total", _fmt_brl(p.get("comissao_total"))],
        ["Valor total geral", _fmt_brl(p.get("valor_total"))],
    ]
    table = Table(data, colWidths=[8.5 * cm, None])
    table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, -2), (-1, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, -2), (-1, -1), _COR_PRIMARIA),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e7eb")),
        ("BACKGROUND", (0, 0), (-1, -3), colors.HexColor("#fafafa")),
        ("LINEABOVE", (0, -2), (-1, -2), 0.5, _COR_PRIMARIA),
    ]))
    return [
        Spacer(1, 2 * mm),
        Paragraph("Resumo", titulo_style),
        table,
    ]


def _bloco_totais_final(styles, totais: dict, multi_prof: bool) -> list:
    """Totais de consultas e procedimentos fixos ao final do relatório."""
    titulo = "Totais do período" if multi_prof else "Totais"
    titulo_style = ParagraphStyle(
        "TotTit",
        parent=styles["Heading2"],
        fontSize=10,
        fontName="Helvetica-Bold",
        textColor=_COR_PRIMARIA,
        spaceBefore=4 * mm,
        spaceAfter=2 * mm,
    )
    data = [
        ["Valor total consultas", _fmt_brl(totais.get("valor_consulta"))],
        ["Comissão total consultas", _fmt_brl(totais.get("comissao_consulta"))],
        ["Valor total procedimentos", _fmt_brl(totais.get("valor_procedimento"))],
        ["Comissão total procedimentos", _fmt_brl(totais.get("comissao_procedimento"))],
        ["Comissão total", _fmt_brl(totais.get("comissao_total"))],
        ["Valor total geral", _fmt_brl(totais.get("valor_total"))],
    ]
    table = Table(data, colWidths=[8 * cm, None])
    table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, -2), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, -1), (-1, -1), 10),
        ("TEXTCOLOR", (0, -2), (-1, -1), _COR_PRIMARIA),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("BOX", (0, 0), (-1, -1), 0.5, _COR_PRIMARIA),
        ("BACKGROUND", (0, 0), (-1, -3), colors.HexColor("#fdf8f9")),
        ("LINEABOVE", (0, -2), (-1, -2), 0.75, _COR_PRIMARIA),
    ]))
    return [
        Spacer(1, 3 * mm),
        HRFlowable(width="100%", thickness=0.75, color=_COR_PRIMARIA),
        Spacer(1, 2 * mm),
        Paragraph(titulo, titulo_style),
        table,
    ]
