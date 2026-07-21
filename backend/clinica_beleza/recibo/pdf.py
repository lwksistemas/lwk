"""Geração de PDF do recibo de pagamento."""
import io

from .context import (
    _linha_documento_loja,
    _linha_tel_cep,
    _linhas_descontos_recibo,
    _linhas_taxa_consulta_recibo,
)


def _gerar_pdf_recibo(ctx: dict) -> bytes:
    """Gera PDF do recibo em formato cupom fiscal com layout profissional."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.pagesizes import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buf = io.BytesIO()
    page_w = 80 * mm
    page_h = 240 * mm
    doc = SimpleDocTemplate(
        buf, pagesize=(page_w, page_h),
        leftMargin=4 * mm, rightMargin=4 * mm,
        topMargin=6 * mm, bottomMargin=6 * mm,
    )

    s_center = ParagraphStyle("c", fontSize=8, alignment=TA_CENTER, leading=11)
    s_bold_center = ParagraphStyle("bc", fontSize=11, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=14)
    s_title = ParagraphStyle("ti", fontSize=9, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=12)
    s_left = ParagraphStyle("l", fontSize=8, leading=11)
    s_bold = ParagraphStyle("b", fontSize=8, fontName="Helvetica-Bold", leading=11)
    s_total = ParagraphStyle("t", fontSize=12, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=15)
    s_footer = ParagraphStyle("f", fontSize=7, alignment=TA_CENTER, leading=10, textColor=colors.HexColor("#666666"))
    s_right = ParagraphStyle("r", fontSize=8, alignment=TA_RIGHT, leading=11)

    hr = HRFlowable(width="100%", thickness=0.5, dash=[2, 2], spaceAfter=3, spaceBefore=3)
    col_w = page_w - 8 * mm
    story = []

    if ctx["loja_nome"]:
        story.append(Paragraph(ctx["loja_nome"].upper(), s_bold_center))
    doc_line = _linha_documento_loja(ctx)
    if doc_line:
        story.append(Paragraph(doc_line, s_center))
    if ctx["loja_endereco"]:
        story.append(Paragraph(ctx["loja_endereco"], s_center))
    tel_cep = ctx.get("loja_tel_cep") or _linha_tel_cep(ctx.get("loja_telefone", ""), ctx.get("loja_cep", ""))
    if tel_cep:
        story.append(Paragraph(tel_cep, s_center))
    if ctx.get("loja_email"):
        story.append(Paragraph(ctx["loja_email"], s_center))
    story.append(Spacer(1, 3 * mm))
    story.append(hr)
    story.append(Paragraph("RECIBO DE PAGAMENTO", s_title))
    story.append(Paragraph(ctx["data"], s_center))
    story.append(hr)

    story.append(Paragraph(f"<b>Cliente:</b> {ctx['paciente_nome']}", s_left))
    if ctx["profissional_nome"]:
        story.append(Paragraph(f"<b>Profissional:</b> {ctx['profissional_nome']}", s_left))
    if ctx.get("data_atendimento"):
        story.append(Paragraph(f"<b>Data/Hora do atendimento:</b> {ctx['data_atendimento']}", s_left))
    story.append(hr)

    story.append(Paragraph("<b>SERVIÇOS</b>", s_bold))
    story.append(Spacer(1, 1 * mm))

    svc_data = []
    linhas_taxa = _linhas_taxa_consulta_recibo(ctx)
    taxa_exibida = linhas_taxa[0][1] if linhas_taxa else 0.0
    for label, valor in linhas_taxa:
        svc_data.append([
            Paragraph(label, s_left),
            Paragraph(f"R$ {valor:.2f}", s_right),
        ])
    for p in ctx["procedimentos"]:
        # Ocultar procedimento redundante: "Consulta" com valor 0 quando taxa já está exibida
        nome_lower = (p["nome"] or "").strip().lower()
        if taxa_exibida > 0 and float(p["valor"]) == 0.0 and nome_lower in ("consulta", "taxa de consulta"):
            continue
        svc_data.append([
            Paragraph(f'• {p["nome"]}', s_left),
            Paragraph(f'R$ {p["valor"]:.2f}', s_right),
        ])

    if svc_data:
        svc_table = Table(svc_data, colWidths=[col_w * 0.65, col_w * 0.35])
        svc_table.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(svc_table)

    story.append(hr)

    totals_data = []
    descontos = _linhas_descontos_recibo(ctx)
    if descontos:
        totals_data.append([
            Paragraph("Subtotal", s_left),
            Paragraph(f'R$ {ctx.get("subtotal", ctx["valor_total"]):.2f}', s_right),
        ])
        for label, valor in descontos:
            totals_data.append([
                Paragraph(label, s_left),
                Paragraph(f"- R$ {valor:.2f}", s_right),
            ])
    totals_data.append([
        Paragraph("<b>Total</b>", s_bold),
        Paragraph(f'<b>R$ {ctx["valor_total"]:.2f}</b>', s_right),
    ])
    formas = ctx.get("formas_pagamento", [])
    valor_pago = ctx.get("valor_pago", 0)
    if formas:
        totals_data.append([Paragraph("<b>Formas de pagamento:</b>", s_bold), Paragraph("", s_right)])
        for f in formas:
            totals_data.append([
                Paragraph(f'  {f["metodo"]}', s_left),
                Paragraph(f'R$ {f["valor"]:.2f}', s_right),
            ])
    elif valor_pago > 0:
        metodo = ctx.get("metodo", "")
        totals_data.append([Paragraph(metodo, s_left), Paragraph(f'R$ {valor_pago:.2f}', s_right)])

    totals_table = Table(totals_data, colWidths=[col_w * 0.55, col_w * 0.45])
    totals_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(totals_table)

    story.append(Spacer(1, 3 * mm))
    if valor_pago > 0:
        story.append(Paragraph(f"VALOR PAGO: R$ {valor_pago:.2f}", s_total))
    if valor_pago >= ctx.get("valor_total", 0) and ctx.get("valor_total", 0) >= 0:
        story.append(Spacer(1, 1 * mm))
        story.append(Paragraph("<b>Quitado</b>", s_center))
    story.append(Spacer(1, 2 * mm))
    story.append(hr)

    aviso = (ctx.get("retorno_aviso") or "").strip()
    if aviso:
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(aviso, s_footer))

    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph("Agradecemos pela confiança!", s_footer))
    story.append(Paragraph("Documento não fiscal — gerado pelo sistema.", s_footer))

    doc.build(story)
    return buf.getvalue()
