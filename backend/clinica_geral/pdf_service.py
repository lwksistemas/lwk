"""PDFs do consultório: evolução, receita ANVISA (duas vias) e guia TISS."""
from io import BytesIO

from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def pdf_response(data: bytes, filename: str, paciente=None) -> HttpResponse:
    if paciente is not None:
        from clinica_beleza.media_docs_service import arquivar_pdf_gerado
        arquivar_pdf_gerado(getattr(paciente, "loja_id", None), paciente, data, filename)
    resp = HttpResponse(data, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{filename}"'
    return resp


def _styles():
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle("t", parent=base["Heading1"], fontSize=13, alignment=TA_CENTER, spaceAfter=8),
        "sub": ParagraphStyle("s", parent=base["Normal"], fontSize=9, alignment=TA_CENTER, textColor=colors.HexColor("#444")),
        "p": ParagraphStyle("p", parent=base["Normal"], fontSize=10, alignment=TA_LEFT, leading=13, spaceAfter=4),
        "small": ParagraphStyle("sm", parent=base["Normal"], fontSize=8, textColor=colors.HexColor("#555")),
    }


def pdf_evolucao(evolucao, consulta, paciente, config) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.6 * cm, bottomMargin=1.6 * cm)
    st = _styles()
    story = [
        Paragraph(getattr(config, "medico_nome", "") or "Consultório", st["titulo"]),
        Paragraph(
            f"{getattr(config, 'especialidade', '') or 'Clínica médica'} · CRM {getattr(config, 'crm', '') or '—'}",
            st["sub"],
        ),
        Spacer(1, 10),
        Paragraph(f"<b>Prontuário</b> {paciente.numero_prontuario or paciente.id} — {paciente.nome}", st["p"]),
        Paragraph(f"Consulta {consulta.data.strftime('%d/%m/%Y')} {consulta.hora.strftime('%H:%M')}", st["p"]),
        Spacer(1, 8),
        Paragraph("<b>S — Subjetivo</b>", st["p"]),
        Paragraph(evolucao.subjetivo or "—", st["p"]),
        Paragraph("<b>O — Objetivo</b>", st["p"]),
        Paragraph(evolucao.objetivo or "—", st["p"]),
        Paragraph("<b>A — Avaliação</b>", st["p"]),
        Paragraph(evolucao.avaliacao or "—", st["p"]),
        Paragraph("<b>P — Plano</b>", st["p"]),
        Paragraph(evolucao.plano or "—", st["p"]),
    ]
    if paciente.alergias:
        story.append(Spacer(1, 8))
        story.append(Paragraph(f"<b>Alergias:</b> {paciente.alergias}", st["p"]))
    doc.build(story)
    return buf.getvalue()


def pdf_receita(prescricao, consulta, paciente, config) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=1.6 * cm, rightMargin=1.6 * cm, topMargin=1.4 * cm, bottomMargin=1.4 * cm)
    st = _styles()
    story = []
    for via, titulo in (("1ª via — Paciente", "RECEITUÁRIO"), ("2ª via — Farmácia", "RECEITUÁRIO")):
        story.extend(_via_receita(st, titulo, via, prescricao, consulta, paciente, config))
        story.append(Spacer(1, 18))
    doc.build(story)
    return buf.getvalue()


def _via_receita(st, titulo, via, prescricao, consulta, paciente, config):
    medico = getattr(config, "medico_nome", "") or "Médico"
    crm = getattr(config, "crm", "") or "—"
    end = getattr(config, "endereco", "") or ""
    itens = list(prescricao.itens.all())
    linhas = [["Medicamento", "Dosagem", "Posologia", "Qtde"]]
    for item in itens:
        linhas.append([item.medicamento, item.dosagem, item.posologia, item.quantidade])
    tabela = Table(linhas, colWidths=[7 * cm, 3 * cm, 5 * cm, 2 * cm])
    tabela.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF2F6")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return [
        Paragraph(titulo, st["titulo"]),
        Paragraph(f"{via} · Padrão ANVISA (uso interno do consultório)", st["sub"]),
        Paragraph(f"{medico} · CRM {crm}", st["p"]),
        Paragraph(end, st["small"]),
        Paragraph(
            f"Paciente: <b>{paciente.nome}</b> · CPF {paciente.cpf or '—'} · "
            f"{consulta.data.strftime('%d/%m/%Y')}",
            st["p"],
        ),
        tabela,
        Spacer(1, 6),
        Paragraph("______________________________", st["sub"]),
        Paragraph("Assinatura e carimbo", st["small"]),
    ]


def pdf_guia_tiss(guia, consulta, paciente, config) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    st = _styles()
    valor = guia.valor if guia.valor is not None else consulta.valor
    story = [
        Paragraph("GUIA DE CONSULTA — PADRÃO TISS", st["titulo"]),
        Paragraph("ANS / uso interno do consultório (impressão)", st["sub"]),
        Spacer(1, 10),
        Paragraph(f"Nº da guia: <b>{guia.numero_guia or guia.id}</b>", st["p"]),
        Paragraph(f"Prestador: {getattr(config, 'medico_nome', '') or 'Consultório'} · CRM {getattr(config, 'crm', '') or '—'}", st["p"]),
        Paragraph(f"Endereço: {getattr(config, 'endereco', '') or '—'}", st["p"]),
        Paragraph(f"Beneficiário: <b>{paciente.nome}</b> · CPF {paciente.cpf or '—'}", st["p"]),
        Paragraph(f"Convênio: {consulta.convenio or 'PARTICULAR'}", st["p"]),
        Paragraph(f"Data: {consulta.data.strftime('%d/%m/%Y')} {consulta.hora.strftime('%H:%M')}", st["p"]),
        Paragraph(f"Procedimento: {guia.codigo_procedimento} — Consulta médica", st["p"]),
        Paragraph(f"Valor: R$ {valor if valor is not None else '—'}", st["p"]),
    ]
    doc.build(story)
    return buf.getvalue()
