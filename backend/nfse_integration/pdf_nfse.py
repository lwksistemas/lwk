"""
Geração de PDF para NFS-e (Nota Fiscal de Serviço Eletrônica).
"""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER
import logging

logger = logging.getLogger(__name__)


def gerar_pdf_nfse(nfse, loja) -> BytesIO:
    """
    Gera PDF da NFS-e.
    
    Args:
        nfse: instância do modelo NFSe
        loja: instância do modelo Loja (prestador)
    
    Returns:
        BytesIO: buffer com o PDF gerado
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm, leftMargin=2*cm, rightMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'NFSeTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#0176d3'),
        alignment=TA_CENTER,
        spaceBefore=0,
        spaceAfter=10,
    )

    section_style = ParagraphStyle(
        'NFSeSection',
        parent=styles['Heading2'],
        fontSize=11,
        spaceBefore=10,
        spaceAfter=4,
    )

    info_style = ParagraphStyle(
        'NFSeInfo',
        parent=styles['Normal'],
        fontSize=9,
        spaceBefore=0,
        spaceAfter=2,
        leading=12,
    )

    # Título
    elements.append(Paragraph('NOTA FISCAL DE SERVIÇO ELETRÔNICA', title_style))
    elements.append(Spacer(1, 0.3*cm))

    # Dados da NFS-e
    elements.append(Paragraph('<b>Dados da Nota Fiscal</b>', section_style))
    nf_data = [
        ['Número NFS-e:', nfse.numero_nf or '—', 'Número RPS:', str(nfse.numero_rps or '—')],
        ['Data Emissão:', nfse.data_emissao.strftime('%d/%m/%Y %H:%M') if nfse.data_emissao else '—', 'Cód. Verificação:', nfse.codigo_verificacao or '—'],
        ['Status:', nfse.get_status_display() if hasattr(nfse, 'get_status_display') else nfse.status, '', ''],
    ]
    t = Table(nf_data, colWidths=[80, 150, 90, 150])
    t.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.3*cm))

    # Prestador
    elements.append(Paragraph('<b>Prestador de Serviços</b>', section_style))
    elements.append(Paragraph(f"<b>Razão Social:</b> {getattr(loja, 'nome', '') or '—'}", info_style))
    elements.append(Paragraph(f"<b>CNPJ:</b> {getattr(loja, 'cpf_cnpj', '') or '—'}", info_style))
    if getattr(loja, 'logradouro', ''):
        endereco_parts = [
            getattr(loja, 'logradouro', '') or '',
            getattr(loja, 'numero', '') or '',
            getattr(loja, 'bairro', '') or '',
            f"{getattr(loja, 'cidade', '') or ''}/{getattr(loja, 'uf', '') or ''}",
        ]
        endereco = ', '.join(p for p in endereco_parts if p)
        elements.append(Paragraph(f"<b>Endereço:</b> {endereco}", info_style))
    elements.append(Spacer(1, 0.2*cm))

    # Tomador
    elements.append(Paragraph('<b>Tomador de Serviços (Cliente)</b>', section_style))
    elements.append(Paragraph(f"<b>Nome/Razão Social:</b> {nfse.tomador_nome or '—'}", info_style))
    elements.append(Paragraph(f"<b>CPF/CNPJ:</b> {nfse.tomador_cpf_cnpj or '—'}", info_style))
    if nfse.tomador_email:
        elements.append(Paragraph(f"<b>Email:</b> {nfse.tomador_email}", info_style))
    elements.append(Spacer(1, 0.2*cm))

    # Serviço — suporta tanto 'servico_descricao' (NFSe da loja) quanto 'descricao_servico' (NFSeEmitida)
    servico_descricao = (
        getattr(nfse, 'servico_descricao', None)
        or getattr(nfse, 'descricao_servico', None)
        or '—'
    )
    servico_codigo = getattr(nfse, 'servico_codigo', None) or getattr(nfse, 'codigo_servico', None)

    elements.append(Paragraph('<b>Descrição do Serviço</b>', section_style))
    elements.append(Paragraph(servico_descricao, info_style))
    if servico_codigo:
        elements.append(Paragraph(f"<b>Código do Serviço:</b> {servico_codigo}", info_style))
    elements.append(Spacer(1, 0.3*cm))

    # Valores
    elements.append(Paragraph('<b>Valores</b>', section_style))
    valor_data = [
        ['Valor dos Serviços:', f'R$ {float(nfse.valor):.2f}'],
        ['Alíquota ISS:', f'{float(nfse.aliquota_iss):.2f}%'],
        ['Valor ISS:', f'R$ {float(nfse.valor_iss):.2f}'],
        ['Valor Líquido:', f'R$ {float(nfse.valor - nfse.valor_iss):.2f}'],
    ]
    t2 = Table(valor_data, colWidths=[120, 120])
    t2.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LINEBELOW', (0, -1), (-1, -1), 1, colors.grey),
    ]))
    elements.append(t2)
    elements.append(Spacer(1, 0.5*cm))

    # Rodapé
    footer_style = ParagraphStyle(
        'NFSeFooter',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER,
    )
    elements.append(Paragraph(
        'Documento auxiliar da Nota Fiscal de Serviço Eletrônica. '
        'Consulte a autenticidade no portal da prefeitura usando o código de verificação.',
        footer_style,
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer
