"""Geração de PDF de laudo (ReportLab). Assinatura ICP-Brasil entra na Fase 1."""
from __future__ import annotations

from io import BytesIO

from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def gerar_pdf_laudo(laudo) -> bytes:
    pedido = laudo.pedido
    paciente = pedido.paciente
    procedimento = pedido.procedimento

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "TitleRad",
        parent=styles["Heading1"],
        fontSize=14,
        spaceAfter=12,
    )
    body = ParagraphStyle(
        "BodyRad",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=8,
    )
    small = ParagraphStyle(
        "SmallRad",
        parent=styles["Normal"],
        fontSize=8,
        textColor="#555555",
    )

    story = []
    story.append(Paragraph("LAUDO DE EXAME DE IMAGEM", title))
    story.append(Paragraph(f"<b>Paciente:</b> {paciente.nome}", body))
    if paciente.cpf:
        story.append(Paragraph(f"<b>CPF:</b> {paciente.cpf}", body))
    story.append(Paragraph(f"<b>Procedimento:</b> {procedimento.nome}", body))
    story.append(Paragraph(f"<b>Accession:</b> {pedido.accession_number}", body))
    if pedido.study_instance_uid:
        story.append(Paragraph(f"<b>Study UID:</b> {pedido.study_instance_uid}", body))
    if pedido.medico_solicitante:
        story.append(
            Paragraph(
                f"<b>Solicitante:</b> {pedido.medico_solicitante}"
                + (f" — CRM {pedido.crm_solicitante}" if pedido.crm_solicitante else ""),
                body,
            )
        )
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("<b>Laudo</b>", body))
    for linha in (laudo.texto or "").splitlines() or ["(sem texto)"]:
        story.append(Paragraph(linha.replace("\n", "<br/>") or "&nbsp;", body))
    if laudo.conclusao:
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph("<b>Conclusão</b>", body))
        story.append(Paragraph(laudo.conclusao.replace("\n", "<br/>"), body))
    if laudo.bi_rads:
        story.append(Paragraph(f"<b>BI-RADS:</b> {laudo.bi_rads}", body))

    story.append(Spacer(1, 1 * cm))
    medico = laudo.medico_laudador or "________________"
    crm = f"CRM {laudo.crm_laudador}" if laudo.crm_laudador else ""
    story.append(Paragraph(f"{medico} {crm}".strip(), body))
    when = laudo.assinado_em or timezone.now()
    story.append(Paragraph(when.strftime("%d/%m/%Y %H:%M"), small))
    story.append(Spacer(1, 0.5 * cm))
    story.append(
        Paragraph(
            "Documento gerado pelo RIS LWK Radiologia. Assinatura ICP-Brasil (nuvem) na Fase 1 do piloto.",
            small,
        )
    )

    doc.build(story)
    return buffer.getvalue()
