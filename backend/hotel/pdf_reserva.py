"""
Geração de PDF para Confirmação de Reserva de Hotel.
Inclui dados do hotel, hóspede, quarto, datas e assinaturas digitais.
"""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import pytz
import logging

logger = logging.getLogger(__name__)


def _ts_local(dt):
    if not dt:
        return '—'
    tz = pytz.timezone('America/Sao_Paulo')
    return dt.astimezone(tz).strftime('%d/%m/%Y %H:%M:%S')


def gerar_pdf_reserva(reserva, incluir_assinaturas: bool = False) -> BytesIO:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('Title2', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#0176d3'), alignment=TA_CENTER)
    subtitle_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10, textColor=colors.grey, alignment=TA_CENTER)

    # Cabeçalho
    elements.append(Paragraph('CONFIRMAÇÃO DE RESERVA', title_style))
    elements.append(Spacer(1, 0.3 * cm))

    # Dados da loja
    from superadmin.models import Loja
    loja = Loja.objects.using('default').filter(id=reserva.loja_id).first()
    if loja:
        elements.append(Paragraph(loja.nome, ParagraphStyle('LojaNome', parent=styles['Normal'], fontSize=14, alignment=TA_CENTER)))
        if loja.cpf_cnpj:
            elements.append(Paragraph(f'CNPJ: {loja.cpf_cnpj}', subtitle_style))
        elements.append(Spacer(1, 0.5 * cm))

    # Dados da reserva
    hospede = reserva.hospede
    quarto = reserva.quarto
    diarias = (reserva.data_checkout - reserva.data_checkin).days if reserva.data_checkin and reserva.data_checkout else 0

    data_reserva = [
        ['Campo', 'Informação'],
        ['Hóspede', hospede.nome if hospede else '—'],
        ['Documento', hospede.documento if hospede else '—'],
        ['Email', hospede.email if hospede else '—'],
        ['Telefone', hospede.telefone if hospede else '—'],
        ['Quarto', f'{quarto.numero} - {quarto.nome or quarto.tipo}' if quarto else '—'],
        ['Check-in', reserva.data_checkin.strftime('%d/%m/%Y') if reserva.data_checkin else '—'],
        ['Check-out', reserva.data_checkout.strftime('%d/%m/%Y') if reserva.data_checkout else '—'],
        ['Diárias', str(diarias)],
        ['Adultos', str(reserva.adultos)],
        ['Crianças', str(reserva.criancas)],
        ['Valor Diária', f'R$ {reserva.valor_diaria:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')],
        ['Valor Total', f'R$ {reserva.valor_total:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')],
    ]
    if reserva.canal:
        data_reserva.append(['Canal', reserva.canal])

    t = Table(data_reserva, colWidths=[6 * cm, 10 * cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0176d3')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.5 * cm))

    # Conteúdo da confirmação
    if reserva.conteudo_confirmacao:
        elements.append(Paragraph('<b>Termos e Condições</b>', styles['Heading2']))
        elements.append(Spacer(1, 0.2 * cm))
        for line in reserva.conteudo_confirmacao.split('\n'):
            if line.strip():
                elements.append(Paragraph(line, styles['Normal']))
        elements.append(Spacer(1, 0.5 * cm))

    # Observações
    if reserva.observacoes:
        elements.append(Paragraph('<b>Observações</b>', styles['Heading2']))
        elements.append(Paragraph(reserva.observacoes, styles['Normal']))
        elements.append(Spacer(1, 0.5 * cm))

    # Assinaturas
    if incluir_assinaturas:
        from .models import ReservaAssinatura
        assinaturas = ReservaAssinatura.objects.filter(reserva=reserva, assinado=True).order_by('tipo')

        if assinaturas.exists():
            elements.append(Spacer(1, 0.5 * cm))
            elements.append(Paragraph('<b>Assinaturas Digitais</b>', styles['Heading2']))
            elements.append(Spacer(1, 0.2 * cm))

            for a in assinaturas:
                tipo_label = 'Hóspede' if a.tipo == 'hospede' else 'Funcionário'
                data_ass = [
                    [f'Assinatura — {tipo_label}', ''],
                    ['Nome', a.nome_assinante],
                    ['Email', a.email_assinante],
                    ['Data/Hora', _ts_local(a.assinado_em)],
                    ['IP', a.ip_address or '—'],
                ]
                ta = Table(data_ass, colWidths=[5 * cm, 11 * cm])
                ta.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('SPAN', (0, 0), (-1, 0)),
                ]))
                elements.append(ta)
                elements.append(Spacer(1, 0.3 * cm))

    # Rodapé legal
    elements.append(Spacer(1, 1 * cm))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    elements.append(Paragraph(
        'Este documento possui validade jurídica e contém as assinaturas digitais de ambas as partes, '
        'com registro de data, hora e endereço IP.',
        footer_style,
    ))
    from django.utils import timezone as tz
    elements.append(Paragraph(f'Gerado em {tz.now().strftime("%d/%m/%Y às %H:%M")}', footer_style))

    doc.build(elements)
    buf.seek(0)
    return buf
