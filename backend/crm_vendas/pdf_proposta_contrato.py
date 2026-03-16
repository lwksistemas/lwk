"""
Geração de PDF para Proposta e Contrato do CRM.
"""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER
import re


def _strip_html(html):
    """Remove tags HTML e retorna texto limpo."""
    if not html:
        return ''
    text = re.sub(r'<[^>]+>', ' ', str(html))
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def gerar_pdf_proposta(proposta) -> BytesIO:
    """Gera PDF da proposta comercial."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'PropostaTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0176d3'),
        spaceAfter=20,
        alignment=TA_CENTER,
    )

    lead_nome = proposta.oportunidade.lead.nome if proposta.oportunidade and proposta.oportunidade.lead else 'Cliente'
    valor = proposta.valor_total
    valor_str = f'R$ {float(valor):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.') if valor else '—'

    elements.append(Paragraph('PROPOSTA COMERCIAL', title_style))
    elements.append(Paragraph(f'<b>Cliente:</b> {lead_nome}', styles['Normal']))
    elements.append(Paragraph(f'<b>Título:</b> {proposta.titulo or "—"}', styles['Normal']))
    elements.append(Paragraph(f'<b>Valor total:</b> {valor_str}', styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))

    conteudo = _strip_html(proposta.conteudo) if proposta.conteudo else 'Conteúdo não informado.'
    elements.append(Paragraph('<b>Conteúdo:</b>', styles['Heading2']))
    elements.append(Paragraph(conteudo[:3000] + ('...' if len(conteudo) > 3000 else ''), styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def gerar_pdf_contrato(contrato) -> BytesIO:
    """Gera PDF do contrato."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'ContratoTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0176d3'),
        spaceAfter=20,
        alignment=TA_CENTER,
    )

    lead_nome = contrato.oportunidade.lead.nome if contrato.oportunidade and contrato.oportunidade.lead else 'Cliente'
    valor = contrato.valor_total
    valor_str = f'R$ {float(valor):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.') if valor else '—'

    elements.append(Paragraph('CONTRATO', title_style))
    elements.append(Paragraph(f'<b>Número:</b> {contrato.numero or "—"}', styles['Normal']))
    elements.append(Paragraph(f'<b>Cliente:</b> {lead_nome}', styles['Normal']))
    elements.append(Paragraph(f'<b>Título:</b> {contrato.titulo or "—"}', styles['Normal']))
    elements.append(Paragraph(f'<b>Valor total:</b> {valor_str}', styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))

    conteudo = _strip_html(contrato.conteudo) if contrato.conteudo else 'Conteúdo não informado.'
    elements.append(Paragraph('<b>Conteúdo:</b>', styles['Heading2']))
    elements.append(Paragraph(conteudo[:3000] + ('...' if len(conteudo) > 3000 else ''), styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer
