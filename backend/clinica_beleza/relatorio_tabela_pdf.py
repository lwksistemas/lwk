"""PDFs tabulares de relatórios (lançamentos, faturamento, comissões agrupadas)."""
from __future__ import annotations

from datetime import date
from io import BytesIO
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .comissao_relatorio_pdf import (
    _CINZA,
    _COR_PRIMARIA,
    _fmt_brl,
    _fmt_data_br,
    _is_linha_consulta,
    _logo_image,
    _make_data_table,
)
from .pdf_common import finalize_pdf_com_timbrado
from .prontuario_pdf import _resolver_cabecalho_relatorio

_MARGEM = 1.5 * cm


def _fmt_iso_br(iso: str | None) -> str:
    if not iso:
        return "—"
    parts = str(iso).split("-")
    if len(parts) != 3:
        return str(iso)
    y, m, d = parts
    return f"{d}/{m}/{y}"


def _cell_style(align=TA_LEFT, bold: bool = False, size: int = 7):
    return ParagraphStyle(
        f"RelCell_{align}_{bold}_{size}",
        fontSize=size,
        leading=size + 2,
        fontName="Helvetica-Bold" if bold else "Helvetica",
        alignment=align,
        textColor=colors.HexColor("#111827"),
    )


_CELL_L = _cell_style(TA_LEFT)
_CELL_R = _cell_style(TA_RIGHT)
_CELL_LB = _cell_style(TA_LEFT, bold=True)
_CELL_RB = _cell_style(TA_RIGHT, bold=True)
_HEAD = _cell_style(TA_LEFT, bold=True, size=6)
_HEAD_R = _cell_style(TA_RIGHT, bold=True, size=6)


def _p(texto, style=None) -> Paragraph:
    raw = texto if texto not in (None, "") else "—"
    return Paragraph(xml_escape(str(raw)), style or _CELL_L)


def _styles_relatorio(styles):
    titulo_style = ParagraphStyle(
        "RelTitulo",
        parent=styles["Heading1"],
        fontSize=13,
        textColor=_COR_PRIMARIA,
        alignment=TA_CENTER,
        spaceAfter=3,
    )
    subtitulo_style = ParagraphStyle(
        "RelSub",
        parent=styles["Normal"],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=_CINZA,
        spaceAfter=1,
    )
    secao_style = ParagraphStyle(
        "RelSecao",
        parent=styles["Heading2"],
        fontSize=10,
        fontName="Helvetica-Bold",
        textColor=_COR_PRIMARIA,
        spaceBefore=3 * mm,
        spaceAfter=1.5 * mm,
    )
    return titulo_style, subtitulo_style, secao_style


def _cabecalho_elements(tipo_cab, dados_cab, titulo_style):
    elements = []
    if tipo_cab == "logo":
        img = _logo_image(dados_cab)
        if img:
            elements.append(img)
            elements.append(Spacer(1, 2 * mm))
    elif tipo_cab == "texto" and dados_cab:
        elements.append(Paragraph(getattr(dados_cab, "nome", "") or "Clínica", titulo_style))
        elements.append(Spacer(1, 1 * mm))
    return elements


def _periodo_elements(titulo, titulo_style, subtitulo_style, data_inicio, data_fim, extra=None):
    elements = [
        Paragraph(titulo, titulo_style),
        Paragraph(
            f"Período: {_fmt_data_br(data_inicio)} a {_fmt_data_br(data_fim)}",
            subtitulo_style,
        ),
    ]
    if extra:
        elements.append(Paragraph(extra, subtitulo_style))
    elements.append(Spacer(1, 2 * mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e5e7eb")))
    elements.append(Spacer(1, 2 * mm))
    return elements


def _iniciar_pdf(loja, *, usar_paisagem: bool):
    tipo_cab, dados_cab = _resolver_cabecalho_relatorio(loja.id)
    page = landscape(A4) if usar_paisagem else A4
    top_margin = 3.2 * cm if tipo_cab == "timbrado" else 1.8 * cm
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    titulo_style, subtitulo_style, secao_style = _styles_relatorio(styles)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=page,
        leftMargin=_MARGEM,
        rightMargin=_MARGEM,
        topMargin=top_margin,
        bottomMargin=1.4 * cm,
    )
    largura = page[0] - (2 * _MARGEM)
    return buffer, doc, styles, titulo_style, subtitulo_style, secao_style, tipo_cab, dados_cab, largura


def _tabela_mista(headers, rows, footer, col_widths, n_texto: int) -> Table:
    """n_texto primeiras colunas alinhadas à esquerda; o restante à direita."""
    head = [
        _p(h, _HEAD if i < n_texto else _HEAD_R)
        for i, h in enumerate(headers)
    ]
    body = []
    for row in rows:
        body.append([
            _p(cell, _CELL_L if i < n_texto else _CELL_R)
            for i, cell in enumerate(row)
        ])
    data = [head] + body
    if footer:
        data.append([
            _p(cell, _CELL_LB if i < n_texto else _CELL_RB)
            for i, cell in enumerate(footer)
        ])
    table = Table(data, colWidths=col_widths, repeatRows=1)
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]
    if footer:
        fr = len(data) - 1
        cmds.append(("BACKGROUND", (0, fr), (-1, fr), colors.HexColor("#fafafa")))
    table.setStyle(TableStyle(cmds))
    return table


def agrupar_comissoes_para_pdf(resultado: dict, chave: str) -> dict:
    """Consolida detalhes de comissão por local ou convênio (mesmo critério da tela)."""
    grupos: dict[str, dict] = {}
    for p in resultado.get("profissionais") or []:
        for d in p.get("detalhes") or []:
            if chave == "local":
                nome = (d.get("local_nome") or "").strip() or "Sem local"
            else:
                nome = (d.get("convenio_nome") or "").strip()
                if not nome:
                    nome = "Particular / sem convênio" if _is_linha_consulta(d) else "Sem convênio"
            g = grupos.setdefault(nome, {
                "nome": nome,
                "total_atendimentos": 0,
                "valor_consulta": 0.0,
                "valor_procedimento": 0.0,
                "valor_total": 0.0,
                "comissao_consulta": 0.0,
                "comissao_procedimento": 0.0,
                "comissao_total": 0.0,
            })
            if _is_linha_consulta(d):
                g["total_atendimentos"] += int(d.get("qtd") or 0)
                g["valor_consulta"] += float(d.get("valor_consulta") or 0)
                g["comissao_consulta"] += float(d.get("comissao_consulta") or 0)
            else:
                g["valor_procedimento"] += float(d.get("valor_procedimento") or 0)
                g["comissao_procedimento"] += float(d.get("comissao_procedimento") or 0)
            g["valor_total"] = g["valor_consulta"] + g["valor_procedimento"]
            g["comissao_total"] = g["comissao_consulta"] + g["comissao_procedimento"]
    linhas = sorted(grupos.values(), key=lambda x: (x["nome"] or "").lower())
    return {"linhas": linhas, "totais": resultado.get("totais") or {}, "agrupamento": chave}


def gerar_pdf_lancamentos(
    *,
    resultado: dict,
    loja,
    data_inicio: date | None,
    data_fim: date | None,
    forma_label: str | None = None,
) -> BytesIO:
    buffer, doc, styles, titulo_style, subtitulo_style, secao_style, tipo_cab, dados_cab, largura = (
        _iniciar_pdf(loja, usar_paisagem=True)
    )
    extra = f"Forma de pagamento: {forma_label}" if forma_label else None
    elements = []
    elements.extend(_cabecalho_elements(tipo_cab, dados_cab, titulo_style))
    elements.extend(_periodo_elements(
        "Lançamentos por profissional", titulo_style, subtitulo_style, data_inicio, data_fim, extra,
    ))

    totais = resultado.get("totais") or {}
    elements.append(Paragraph(
        f'{totais.get("total_atendimentos", 0)} atendimentos · '
        f'Total {_fmt_brl(totais.get("valor_total"))} · '
        f'Comissão {_fmt_brl(totais.get("comissao_total"))}',
        subtitulo_style,
    ))
    elements.append(Spacer(1, 2 * mm))

    profissionais = resultado.get("profissionais") or []
    if not profissionais:
        elements.append(Paragraph("Nenhum lançamento no período.", styles["Normal"]))
    else:
        col_w = [
            largura * 0.09,
            largura * 0.20,
            largura * 0.27,
            largura * 0.14,
            largura * 0.10,
            largura * 0.10,
            largura * 0.10,
        ]
        headers = ["Data", "Paciente", "Procedimentos", "Convênio", "Forma", "Valor", "Comissão"]
        for p in profissionais:
            n = p.get("total_atendimentos") or 0
            elements.append(Paragraph(
                f'{p.get("nome") or "—"} — {n} paciente{"s" if n != 1 else ""} · {_fmt_brl(p.get("valor_total"))}',
                secao_style,
            ))
            rows = [
                [
                    _fmt_iso_br(l.get("data")),
                    l.get("paciente") or "—",
                    l.get("procedimentos") or "—",
                    l.get("convenio") or "—",
                    l.get("forma_pagamento_label") or l.get("forma_pagamento") or "—",
                    _fmt_brl(l.get("valor")),
                    _fmt_brl(l.get("comissao")),
                ]
                for l in (p.get("lancamentos") or [])
            ]
            footer = [
                "Total",
                "",
                "",
                "",
                "",
                _fmt_brl(p.get("valor_total")),
                _fmt_brl(p.get("comissao_total")),
            ]
            elements.append(_tabela_mista(headers, rows, footer, col_w, n_texto=5))

    doc.build(elements)
    buffer.seek(0)
    return finalize_pdf_com_timbrado(buffer, tipo_cab, dados_cab)


_FATURAMENTO_TITULO = {
    "profissional": "Faturamento por Profissional",
    "procedimento": "Faturamento por Procedimento",
    "local": "Faturamento por Local de Atendimento",
    "convenio": "Faturamento por Convênio",
}

_FATURAMENTO_COLUNA = {
    "profissional": "Profissional",
    "procedimento": "Procedimento",
    "local": "Local de Atendimento",
    "convenio": "Convênio",
}

_COMISSAO_AGRUPADO_TITULO = {
    "local": "Comissão por Local de Atendimento",
    "convenio": "Comissão por Convênio",
}


def gerar_pdf_faturamento(
    *,
    resultado: dict,
    loja,
    data_inicio: date | None,
    data_fim: date | None,
    agrupar: str = "profissional",
) -> BytesIO:
    buffer, doc, styles, titulo_style, subtitulo_style, secao_style, tipo_cab, dados_cab, largura = (
        _iniciar_pdf(loja, usar_paisagem=False)
    )
    titulo = _FATURAMENTO_TITULO.get(agrupar, "Faturamento")
    col_nome = _FATURAMENTO_COLUNA.get(agrupar, "Nome")
    elements = []
    elements.extend(_cabecalho_elements(tipo_cab, dados_cab, titulo_style))
    elements.extend(_periodo_elements(titulo, titulo_style, subtitulo_style, data_inicio, data_fim))

    linhas = resultado.get("linhas") or []
    totais = resultado.get("totais") or {}
    if not linhas:
        elements.append(Paragraph("Nenhum dado no período selecionado.", styles["Normal"]))
    else:
        headers = [col_nome, "Atendimentos", "Consultas", "Procedimentos", "Total"]
        rows = [
            [
                (ln.get("nome") or "—")[:80],
                str(ln.get("total_atendimentos") or 0),
                _fmt_brl(ln.get("valor_consulta")),
                _fmt_brl(ln.get("valor_procedimento")),
                _fmt_brl(ln.get("valor_total")),
            ]
            for ln in linhas
        ]
        footer = [
            "Total",
            str(totais.get("total_atendimentos") or 0),
            _fmt_brl(totais.get("valor_consulta")),
            _fmt_brl(totais.get("valor_procedimento")),
            _fmt_brl(totais.get("valor_total")),
        ]
        col_w = [largura * 0.36, largura * 0.14, largura * 0.16, largura * 0.17, largura * 0.17]
        elements.append(_make_data_table(headers, rows, footer, col_widths=col_w, font_size=8))

    doc.build(elements)
    buffer.seek(0)
    return finalize_pdf_com_timbrado(buffer, tipo_cab, dados_cab)


def gerar_pdf_comissoes_agrupado(
    *,
    resultado: dict,
    loja,
    data_inicio: date | None,
    data_fim: date | None,
    agrupar: str,
) -> BytesIO:
    agrupado = agrupar_comissoes_para_pdf(resultado, agrupar)
    buffer, doc, styles, titulo_style, subtitulo_style, secao_style, tipo_cab, dados_cab, largura = (
        _iniciar_pdf(loja, usar_paisagem=True)
    )
    titulo = _COMISSAO_AGRUPADO_TITULO.get(agrupar, "Comissões")
    col_nome = "Local" if agrupar == "local" else "Convênio"
    elements = []
    elements.extend(_cabecalho_elements(tipo_cab, dados_cab, titulo_style))
    elements.extend(_periodo_elements(titulo, titulo_style, subtitulo_style, data_inicio, data_fim))

    linhas = agrupado.get("linhas") or []
    totais = agrupado.get("totais") or {}
    if not linhas:
        elements.append(Paragraph("Nenhum dado no período selecionado.", styles["Normal"]))
    else:
        headers = [
            col_nome, "Consultas", "Valor cons.", "Com. cons.",
            "Valor proc.", "Com. proc.", "Valor total", "Com. total",
        ]
        rows = [
            [
                (ln.get("nome") or "—")[:60],
                str(ln.get("total_atendimentos") or 0),
                _fmt_brl(ln.get("valor_consulta")),
                _fmt_brl(ln.get("comissao_consulta")),
                _fmt_brl(ln.get("valor_procedimento")),
                _fmt_brl(ln.get("comissao_procedimento")),
                _fmt_brl(ln.get("valor_total")),
                _fmt_brl(ln.get("comissao_total")),
            ]
            for ln in linhas
        ]
        footer = [
            "Total",
            str(totais.get("total_atendimentos") or 0),
            _fmt_brl(totais.get("valor_consulta")),
            _fmt_brl(totais.get("comissao_consulta")),
            _fmt_brl(totais.get("valor_procedimento")),
            _fmt_brl(totais.get("comissao_procedimento")),
            _fmt_brl(totais.get("valor_total")),
            _fmt_brl(totais.get("comissao_total")),
        ]
        col_w = [
            largura * 0.22,
            largura * 0.08,
            largura * 0.12,
            largura * 0.11,
            largura * 0.12,
            largura * 0.11,
            largura * 0.12,
            largura * 0.12,
        ]
        elements.append(_make_data_table(headers, rows, footer, col_widths=col_w, font_size=7))

    doc.build(elements)
    buffer.seek(0)
    return finalize_pdf_com_timbrado(buffer, tipo_cab, dados_cab)
