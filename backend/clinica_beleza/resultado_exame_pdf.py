"""PDF de impressão da análise de resultado de exame (padrão prontuário/timbrado)."""
from __future__ import annotations

from io import BytesIO
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from .prontuario_pdf.elements import (
    _build_consulta_meta_elements,
    _build_rodape_impressao,
    _format_datetime_br,
)
from .prontuario_pdf.generators import _build_pdf
from .prontuario_pdf.styles import _get_styles
from .resultado_exame_service import montar_comparacao_resultado

_AVISO_PADRAO = (
    "A sugestão usa a faixa do laudo ou o catálogo interno conforme sexo e idade "
    "do cadastro — não substitui a avaliação profissional."
)

_STATUS_ROTULO = {
    "alto": "Acima",
    "baixo": "Abaixo",
    "dentro": "Dentro da faixa",
    "sem_referencia": "Sem referência",
}

_EVOLUCAO_ROTULO = {
    "melhorou": "Melhorou",
    "piorou": "Piorou",
    "estavel": "Estável",
}


def _fmt_num(valor) -> str:
    if valor is None:
        return "—"
    try:
        n = float(valor)
    except (TypeError, ValueError):
        return str(valor)
    if abs(n - round(n)) < 1e-9:
        return str(int(round(n)))
    texto = f"{n:.4f}".rstrip("0").rstrip(".")
    return texto.replace(".", ",")


def _fmt_faixa(marcador: dict) -> str:
    fmin = marcador.get("faixa_min")
    fmax = marcador.get("faixa_max")
    if fmin is None and fmax is None:
        return "—"
    if fmin is None:
        return f"até {_fmt_num(fmax)}"
    if fmax is None:
        return f"≥ {_fmt_num(fmin)}"
    return f"{_fmt_num(fmin)} – {_fmt_num(fmax)}"


def gerar_pdf_resultado_exame(consulta, resultado) -> BytesIO:
    """Gera PDF A4 da análise (tabela + aviso), com logo/timbrado da clínica."""
    styles = _get_styles()
    loja_id = consulta.loja_id
    elements = _build_consulta_meta_elements(consulta, "Análise de resultado de exame", styles)

    nome_arquivo = xml_escape((getattr(resultado, "nome_arquivo", None) or "laudo.pdf")[:120])
    quando = _format_datetime_br(getattr(resultado, "created_at", None))
    elements.append(Paragraph(f"<b>Arquivo:</b> {nome_arquivo}", styles["DocBody"]))
    if quando:
        elements.append(Paragraph(f"<b>Importado em:</b> {quando}", styles["DocBody"]))
    elements.append(Spacer(1, 3 * mm))

    aviso = (getattr(resultado, "aviso_cadastro", None) or "").strip()
    if aviso:
        elements.append(Paragraph(xml_escape(aviso), styles["DocBody"]))
        elements.append(Spacer(1, 2 * mm))

    elements.append(Paragraph(xml_escape(_AVISO_PADRAO), styles["DocBody"]))
    elements.append(Spacer(1, 4 * mm))

    marcadores = list(getattr(resultado, "marcadores", None) or [])
    if not marcadores:
        elements.append(
            Paragraph(
                "Nenhum biomarcador reconhecido automaticamente. Avalie o laudo original.",
                styles["DocBody"],
            )
        )
    else:
        rows = [["Exame", "Valor", "Referência", "Sugestão"]]
        for item in marcadores:
            nome = xml_escape(str(item.get("nome") or item.get("codigo") or "—"))
            unidade = xml_escape(str(item.get("unidade") or "").strip())
            valor = f"{_fmt_num(item.get('valor'))} {unidade}".strip()
            status = _STATUS_ROTULO.get(str(item.get("status") or ""), str(item.get("status") or "—"))
            rows.append([nome, valor, _fmt_faixa(item), status])

        table = Table(rows, colWidths=[150, 95, 95, 90])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 4 * mm))

        comparacao = montar_comparacao_resultado(resultado)
        if comparacao and comparacao.get("itens"):
            elements.append(Paragraph("<b>Evolução em relação ao laudo anterior</b>", styles["DocTitle"]))
            elements.append(Paragraph(xml_escape(comparacao.get("texto") or ""), styles["DocBody"]))
            elements.append(Spacer(1, 2 * mm))
            rows_ev = [["Exame", "Anterior", "Atual", "Δ", "Evolução"]]
            for item in comparacao["itens"]:
                delta = item.get("delta")
                pct = item.get("delta_pct")
                delta_txt = _fmt_num(delta)
                if pct is not None:
                    sinal = "+" if pct > 0 else ""
                    delta_txt = f"{delta_txt} ({sinal}{_fmt_num(pct)}%)"
                unidade = xml_escape(str(item.get("unidade") or "").strip())
                rows_ev.append([
                    xml_escape(str(item.get("nome") or "")),
                    f"{_fmt_num(item.get('valor_anterior'))} {unidade}".strip(),
                    f"{_fmt_num(item.get('valor_atual'))} {unidade}".strip(),
                    delta_txt,
                    _EVOLUCAO_ROTULO.get(str(item.get("evolucao") or ""), str(item.get("evolucao") or "—")),
                ])
            table_ev = Table(rows_ev, colWidths=[120, 85, 85, 85, 70])
            table_ev.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 3),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                )
            )
            elements.append(table_ev)
            elements.append(Spacer(1, 4 * mm))

        fora = [m for m in marcadores if m.get("status") in ("alto", "baixo")]
        if fora:
            elements.append(Paragraph("<b>Fora da referência</b>", styles["DocTitle"]))
            elements.append(
                Paragraph(
                    "Sintomas possíveis e recomendações de apoio (educativos — não substituem avaliação profissional).",
                    styles["DocBody"],
                )
            )
            elements.append(Spacer(1, 2 * mm))
            for item in fora:
                rotulo = _STATUS_ROTULO.get(item.get("status") or "", item.get("status") or "")
                linha = (
                    f"<b>{xml_escape(str(item.get('nome') or ''))}</b>: "
                    f"{_fmt_num(item.get('valor'))} {xml_escape(str(item.get('unidade') or ''))} "
                    f"({rotulo}; ref. {_fmt_faixa(item)})"
                )
                elements.append(Paragraph(linha.strip(), styles["DocBody"]))
                sintomas = [str(s).strip() for s in (item.get("sintomas_possiveis") or []) if str(s).strip()]
                recomendacoes = [str(s).strip() for s in (item.get("recomendacoes") or []) if str(s).strip()]
                if sintomas:
                    elements.append(Paragraph("<b>Sintomas possíveis</b>", styles["DocBody"]))
                    for s in sintomas:
                        elements.append(Paragraph(f"• {xml_escape(s)}", styles["DocBody"]))
                if recomendacoes:
                    elements.append(Paragraph("<b>Recomendações de apoio</b>", styles["DocBody"]))
                    for s in recomendacoes:
                        elements.append(Paragraph(f"• {xml_escape(s)}", styles["DocBody"]))
                elements.append(Spacer(1, 2 * mm))
            elements.append(Spacer(1, 2 * mm))

    elements.extend(_build_rodape_impressao(styles))
    return _build_pdf(loja_id, elements)
