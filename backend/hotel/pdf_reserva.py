"""
Geração de PDF para Confirmação de Reserva de Hotel.
Inclui: dados do hotel, hóspede, quarto, datas, regras/termos e assinaturas digitais.
"""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import pytz
import logging

logger = logging.getLogger(__name__)

AZUL = colors.HexColor('#0176d3')
VERDE = colors.HexColor('#10b981')


def _ts_local(dt):
    if not dt:
        return '—'
    tz = pytz.timezone('America/Sao_Paulo')
    return dt.astimezone(tz).strftime('%d/%m/%Y %H:%M:%S')


def _fmt_brl(valor):
    if not valor:
        return 'R$ 0,00'
    return f'R$ {float(valor):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def gerar_pdf_reserva(reserva, incluir_assinaturas: bool = False) -> BytesIO:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm,
                            leftMargin=2 * cm, rightMargin=2 * cm)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('Title2', parent=styles['Heading1'], fontSize=20,
                                 textColor=AZUL, alignment=TA_CENTER, spaceAfter=6)
    subtitle_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10,
                                    textColor=colors.grey, alignment=TA_CENTER)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=13,
                                   textColor=AZUL, spaceBefore=12, spaceAfter=6)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10,
                                leading=14, spaceAfter=4)
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8,
                                  textColor=colors.grey, alignment=TA_CENTER)

    # =====================================================================
    # CABEÇALHO
    # =====================================================================
    from superadmin.models import Loja
    loja = Loja.objects.using('default').filter(id=reserva.loja_id).first()

    # 1. Nome do hotel
    nome_hotel = loja.nome if loja else 'Hotel'
    elements.append(Paragraph(nome_hotel, ParagraphStyle('LN', parent=styles['Normal'],
                                                         fontSize=16, alignment=TA_CENTER,
                                                         textColor=AZUL, spaceAfter=2)))

    # 2. Endereço / CNPJ abaixo do nome
    if loja:
        partes_loja = []
        if loja.cpf_cnpj:
            partes_loja.append(f'CNPJ: {loja.cpf_cnpj}')
        rua = ', '.join(p for p in [loja.logradouro, loja.numero] if p and str(p).strip())
        if getattr(loja, 'complemento', '') and str(loja.complemento).strip():
            rua = f'{rua}, {loja.complemento.strip()}' if rua else loja.complemento.strip()
        cidade_uf = ' - '.join(p for p in [loja.cidade, loja.uf] if p and str(p).strip())
        cep_str = f'CEP {loja.cep}' if getattr(loja, 'cep', '') and str(loja.cep).strip() else ''
        endereco_parts = [rua, loja.bairro, cidade_uf, cep_str]
        endereco = ', '.join(p for p in endereco_parts if p and str(p).strip())
        if endereco:
            partes_loja.append(endereco)
        if partes_loja:
            elements.append(Paragraph(' | '.join(partes_loja), subtitle_style))

    # 3. Título do documento
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph('CONFIRMAÇÃO DE RESERVA', title_style))
    elements.append(Spacer(1, 0.3 * cm))

    # =====================================================================
    # DADOS DA RESERVA
    # =====================================================================
    elements.append(Paragraph('Dados da Reserva', section_style))

    hospede = reserva.hospede
    quarto = reserva.quarto
    diarias = (reserva.data_checkout - reserva.data_checkin).days if reserva.data_checkin and reserva.data_checkout else 0

    col1 = 5.5 * cm
    col2 = 11 * cm
    data_reserva = [
        ['Hóspede', hospede.nome if hospede else '—'],
        ['Documento', hospede.documento if hospede and hospede.documento else '—'],
        ['Email', hospede.email if hospede and hospede.email else '—'],
        ['Telefone', hospede.telefone if hospede and hospede.telefone else '—'],
        ['Quarto', f'{quarto.numero} — {quarto.nome or quarto.tipo or ""}' if quarto else '—'],
        ['Check-in', reserva.data_checkin.strftime('%d/%m/%Y') if reserva.data_checkin else '—'],
        ['Check-out', reserva.data_checkout.strftime('%d/%m/%Y') if reserva.data_checkout else '—'],
        ['Diárias', str(diarias)],
        ['Hóspedes', f'{reserva.adultos} adulto(s)' + (f', {reserva.criancas} criança(s)' if reserva.criancas else '')],
        ['Valor Diária', _fmt_brl(reserva.valor_diaria)],
        ['Valor Total', _fmt_brl(reserva.valor_total)],
    ]
    if reserva.canal:
        data_reserva.append(['Canal', reserva.canal])

    t = Table(data_reserva, colWidths=[col1, col2])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#444444')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t)

    # =====================================================================
    # OBSERVAÇÕES
    # =====================================================================
    if reserva.observacoes and reserva.observacoes.strip():
        elements.append(Spacer(1, 0.4 * cm))
        elements.append(Paragraph('Observações', section_style))
        elements.append(Paragraph(reserva.observacoes, body_style))

    # =====================================================================
    # DECLARAÇÃO DE ACEITE
    # =====================================================================
    elements.append(Spacer(1, 0.5 * cm))
    aceite_style = ParagraphStyle('Aceite', parent=body_style, fontSize=9,
                                  textColor=colors.HexColor('#555555'), leading=13)
    elements.append(Paragraph(
        'Ao assinar digitalmente este documento, o hóspede declara ter lido e aceito '
        'todas as regras, termos e condições do hotel, bem como os dados da reserva informados.',
        aceite_style,
    ))

    # =====================================================================
    # ASSINATURAS DIGITAIS
    # =====================================================================
    if incluir_assinaturas:
        from .models import ReservaAssinatura
        assinaturas = ReservaAssinatura.objects.filter(reserva=reserva, assinado=True).order_by('tipo')

        if assinaturas.exists():
            elements.append(Spacer(1, 0.6 * cm))
            elements.append(Paragraph('Assinaturas Digitais', section_style))

            for a in assinaturas:
                tipo_label = 'HÓSPEDE' if a.tipo == 'hospede' else 'FUNCIONÁRIO DO HOTEL'
                data_ass = [
                    [f'Assinatura Digital — {tipo_label}', ''],
                    ['Nome', a.nome_assinante],
                    ['Email', a.email_assinante],
                    ['Data/Hora', _ts_local(a.assinado_em)],
                    ['Endereço IP', a.ip_address or '—'],
                ]
                ta = Table(data_ass, colWidths=[col1, col2])
                ta.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), VERDE),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
                    ('SPAN', (0, 0), (-1, 0)),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0fdf4')),
                ]))
                elements.append(ta)
                elements.append(Spacer(1, 0.3 * cm))

    # =====================================================================
    # RODAPÉ LEGAL
    # =====================================================================
    elements.append(Spacer(1, 1 * cm))
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
