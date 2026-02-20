#!/usr/bin/env python3
"""
Gera o PDF do relatório de capacidade (docs/CAPACIDADE_100_LOJAS.md).
Uso: python scripts/gerar_pdf_capacidade.py
Requer: pip install reportlab
"""
import os
import re
import sys

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError:
    print("Instale o reportlab: pip install reportlab")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
MD_PATH = os.path.join(ROOT_DIR, "docs", "CAPACIDADE_100_LOJAS.md")
OUT_PATH = os.path.join(ROOT_DIR, "docs", "CAPACIDADE_100_LOJAS.pdf")


def md_to_flowables(md_text):
    """Converte markdown simplificado em elementos ReportLab."""
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=12,
    )
    h1_style = ParagraphStyle(
        "CustomH1",
        parent=styles["Heading1"],
        fontSize=14,
        spaceAfter=8,
        spaceBefore=12,
    )
    h2_style = ParagraphStyle(
        "CustomH2",
        parent=styles["Heading2"],
        fontSize=12,
        spaceAfter=6,
        spaceBefore=10,
    )
    normal_style = styles["Normal"]
    flowables = []

    lines = md_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    i = 0
    in_table = False
    table_rows = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Título principal (primeira linha # )
        if i == 0 and stripped.startswith("# "):
            flowables.append(Paragraph(stripped[2:].strip(), title_style))
            flowables.append(Spacer(1, 6 * mm))
            i += 1
            continue

        # ## Seção
        if stripped.startswith("## "):
            if in_table:
                flowables.append(_make_table(table_rows))
                table_rows = []
                in_table = False
            flowables.append(Paragraph(stripped[3:].strip(), h1_style))
            i += 1
            continue

        # ### Subseção
        if stripped.startswith("### "):
            if in_table:
                flowables.append(_make_table(table_rows))
                table_rows = []
                in_table = False
            flowables.append(Paragraph(stripped[4:].strip(), h2_style))
            i += 1
            continue

        # Linha horizontal ---
        if stripped == "---":
            flowables.append(Spacer(1, 4 * mm))
            i += 1
            continue

        # Início de tabela (| algo | algo |)
        if stripped.startswith("|") and "|" in stripped[1:]:
            if not in_table:
                in_table = True
                table_rows = []
            row = [cell.strip().replace("**", "") for cell in stripped.split("|")[1:-1]]
            table_rows.append(row)
            i += 1
            continue

        # Fora de tabela: parágrafo ou lista
        if in_table and stripped == "":
            flowables.append(_make_table(table_rows))
            table_rows = []
            in_table = False
            i += 1
            continue

        if in_table and not stripped.startswith("|"):
            flowables.append(_make_table(table_rows))
            table_rows = []
            in_table = False

        # Lista numerada
        if re.match(r"^\d+\.\s", stripped):
            text = re.sub(r"^\d+\.\s+", "", stripped)
            text = _bold_to_reportlab(text)
            flowables.append(Paragraph(f"• {text}", normal_style))
            i += 1
            continue

        # Lista com -
        if stripped.startswith("- "):
            text = _bold_to_reportlab(stripped[2:])
            flowables.append(Paragraph(f"• {text}", normal_style))
            i += 1
            continue

        # Bloco de código ```text
        if stripped.startswith("```"):
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i].replace("<", "&lt;"))
                i += 1
            if i < len(lines):
                i += 1
            code_style = ParagraphStyle(
                "Code",
                parent=normal_style,
                fontName="Courier",
                fontSize=9,
                backColor=colors.HexColor("#f5f5f5"),
                leftIndent=20,
                rightIndent=20,
                spaceBefore=4,
                spaceAfter=4,
            )
            flowables.append(Paragraph("<br/>".join(code_lines), code_style))
            continue

        # Parágrafo normal
        if stripped:
            text = _bold_to_reportlab(stripped)
            flowables.append(Paragraph(text, normal_style))
        else:
            flowables.append(Spacer(1, 3 * mm))

        i += 1

    if in_table and table_rows:
        flowables.append(_make_table(table_rows))

    return flowables


def _bold_to_reportlab(text):
    """Substitui **texto** por <b>texto</b>."""
    return re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)


def _make_table(rows):
    if not rows:
        return Spacer(1, 2 * mm)
    # Separar header (primeira linha) do body; pular linha de |---|
    data = [r for r in rows if not all(re.match(r"^[\s\-:]+$", c) for c in r)]
    if not data:
        return Spacer(1, 2 * mm)
    t = Table(data, colWidths=[70 * mm, 100 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return t


def main():
    if not os.path.exists(MD_PATH):
        print(f"Arquivo não encontrado: {MD_PATH}")
        sys.exit(1)

    with open(MD_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()

    flowables = md_to_flowables(md_text)

    doc = SimpleDocTemplate(
        OUT_PATH,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    doc.build(flowables)
    print(f"PDF gerado: {OUT_PATH}")


if __name__ == "__main__":
    main()
