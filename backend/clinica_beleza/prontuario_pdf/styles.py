"""Estilos ReportLab para PDFs do prontuário."""
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm


def _get_styles():
    """Retorna estilos customizados para os PDFs do prontuário."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "ClinicaHeader",
        parent=styles["Normal"],
        fontSize=14,
        leading=18,
        alignment=1,  # center
        spaceAfter=2 * mm,
        fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        "ClinicaSubHeader",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        alignment=1,
        spaceAfter=4 * mm,
        textColor=colors.grey,
    ))
    styles.add(ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontSize=12,
        leading=15,
        fontName="Helvetica-Bold",
        spaceAfter=4 * mm,
    ))
    styles.add(ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=3 * mm,
    ))
    styles.add(ParagraphStyle(
        "DocFooter",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        spaceAfter=2 * mm,
        textColor=colors.HexColor("#444444"),
    ))
    styles.add(ParagraphStyle(
        "SectionTitle",
        parent=styles["Normal"],
        fontSize=13,
        leading=16,
        fontName="Helvetica-Bold",
        spaceBefore=6 * mm,
        spaceAfter=3 * mm,
        textColor=colors.HexColor("#333333"),
    ))
    return styles
