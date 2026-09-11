"""PDF do pedido de compra — timbrado da clínica, senão logo."""
from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from xml.sax.saxutils import escape

from clinica_beleza.pdf_common import finalize_pdf_com_timbrado
from clinica_beleza.prontuario_pdf.header import (
    _build_header_elements,
    _resolver_cabecalho,
    get_top_margin,
)


def _styles():
    base = getSampleStyleSheet()
    return {
        "ClinicaHeader": ParagraphStyle(
            "ClinicaHeader", parent=base["Heading2"], fontSize=13, spaceAfter=2,
        ),
        "ClinicaSubHeader": ParagraphStyle(
            "ClinicaSubHeader", parent=base["Normal"], fontSize=8, textColor=colors.grey,
        ),
        "Title": ParagraphStyle("PedTitle", parent=base["Heading1"], fontSize=14, spaceAfter=8),
        "Body": ParagraphStyle("PedBody", parent=base["Normal"], fontSize=9, leading=12),
        "Meta": ParagraphStyle("PedMeta", parent=base["Normal"], fontSize=9, leading=12),
        "Small": ParagraphStyle("PedSmall", parent=base["Normal"], fontSize=8, textColor=colors.grey),
    }


def _brl(valor: Decimal) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def gerar_pdf_pedido_compra(pedido) -> bytes:
    from .models.fornecedores import PedidoCompraAssinatura

    loja_id = pedido.loja_id
    tipo_cab, dados_cab = _resolver_cabecalho(loja_id)
    styles = _styles()
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.6 * cm,
        rightMargin=1.6 * cm,
        topMargin=get_top_margin(loja_id),
        bottomMargin=1.6 * cm,
    )
    story = []
    story.extend(_build_header_elements(loja_id, styles))
    story.append(Paragraph(f"Pedido de compra nº {pedido.numero}", styles["Title"]))

    forn = pedido.fornecedor
    story.append(Paragraph(f"<b>Fornecedor:</b> {escape(forn.razao_social)}", styles["Meta"]))
    if forn.nome_fantasia:
        story.append(Paragraph(f"Nome fantasia: {escape(forn.nome_fantasia)}", styles["Meta"]))
    story.append(Paragraph(f"CNPJ: {escape(forn.cnpj)}", styles["Meta"]))
    end = " ".join(p for p in [forn.logradouro, forn.numero, forn.bairro, forn.municipio, forn.uf] if p)
    if end:
        story.append(Paragraph(escape(end), styles["Small"]))
    story.append(Spacer(1, 8))

    rows = [["Código", "Produto", "Un.", "Qtd", "Preço", "Subtotal"]]
    for item in pedido.itens.all():
        rows.append([
            item.codigo,
            item.nome,
            item.unidade or "un",
            f"{item.quantidade:g}",
            _brl(item.preco),
            _brl(item.subtotal),
        ])
    rows.append(["", "", "", "", "Total", _brl(pedido.valor_total)])
    table = Table(rows, colWidths=[70, 180, 40, 45, 70, 75])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    story.append(table)

    if pedido.observacoes:
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>Observações:</b> {escape(pedido.observacoes)}", styles["Body"]))

    story.append(Spacer(1, 16))
    story.append(Paragraph("<b>Assinaturas</b>", styles["Meta"]))
    for tipo, rotulo in (
        (PedidoCompraAssinatura.TIPO_CLINICA, "Clínica"),
        (PedidoCompraAssinatura.TIPO_FORNECEDOR, "Fornecedor"),
    ):
        ass = pedido.assinaturas.filter(tipo=tipo, assinado=True).first()
        if ass:
            quando = ass.assinado_em.strftime("%d/%m/%Y %H:%M") if ass.assinado_em else ""
            story.append(Paragraph(
                f"{rotulo}: {escape(ass.nome_assinante or '—')} — assinado em {quando}",
                styles["Small"],
            ))
        else:
            story.append(Paragraph(f"{rotulo}: pendente", styles["Small"]))

    doc.build(story)
    out = finalize_pdf_com_timbrado(buf, tipo_cab, dados_cab)
    return out.getvalue()
