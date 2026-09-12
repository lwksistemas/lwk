"""PDF do pedido de compra — logo da clínica + dados da profissional e da loja."""
from decimal import Decimal
from io import BytesIO

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from xml.sax.saxutils import escape

from clinica_beleza.pdf_common import logo_image


VINHO = colors.HexColor("#8B3D52")


def _styles():
    base = getSampleStyleSheet()
    return {
        "NomeClinica": ParagraphStyle(
            "PedNomeClinica", parent=base["Heading2"], fontSize=14, textColor=VINHO, spaceAfter=2,
        ),
        "ClinicaSub": ParagraphStyle(
            "PedClinicaSub", parent=base["Normal"], fontSize=8, textColor=colors.HexColor("#4b5563"), leading=11,
        ),
        "Title": ParagraphStyle("PedTitle", parent=base["Heading1"], fontSize=15, textColor=VINHO, spaceAfter=10),
        "Body": ParagraphStyle("PedBody", parent=base["Normal"], fontSize=9, leading=12),
        "Meta": ParagraphStyle("PedMeta", parent=base["Normal"], fontSize=9, leading=12),
        "Small": ParagraphStyle("PedSmall", parent=base["Normal"], fontSize=8, textColor=colors.HexColor("#4b5563"), leading=11),
        "BoxTitle": ParagraphStyle(
            "PedBoxTitle", parent=base["Normal"], fontSize=8, textColor=VINHO, fontName="Helvetica-Bold",
        ),
    }


def _brl(valor: Decimal) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _cabecalho_clinica(loja: dict, styles):
    """Logo à esquerda (no lugar do QR da receita) e dados da clínica à direita."""
    logo = logo_image(loja.get("logo") or "", max_w=4.2 * cm, max_h=2.4 * cm) if loja.get("logo") else None
    linhas = [f"<b>{escape(loja.get('nome') or 'Clínica')}</b>"]
    if loja.get("cnpj"):
        linhas.append(f"CNPJ: {escape(loja['cnpj'])}")
    if loja.get("endereco"):
        linhas.append(escape(loja["endereco"]))
    extra = []
    if loja.get("telefone"):
        extra.append(escape(loja["telefone"]))
    if loja.get("email"):
        extra.append(escape(loja["email"]))
    if extra:
        linhas.append(" · ".join(extra))
    texto = Paragraph("<br/>".join(linhas), styles["ClinicaSub"])
    if logo:
        tab = Table([[logo, texto]], colWidths=[4.6 * cm, 13.2 * cm])
    else:
        tab = Table([[Paragraph(loja.get("nome") or "Clínica", styles["NomeClinica"])], [texto]], colWidths=[17.8 * cm])
    tab.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return tab


def gerar_pdf_pedido_compra(pedido) -> bytes:
    from .models.fornecedores import PedidoCompraAssinatura
    from .pedido_compra_service import _dados_loja

    loja = _dados_loja(pedido.loja_id)
    styles = _styles()
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.6 * cm,
        rightMargin=1.6 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.6 * cm,
    )
    story = [_cabecalho_clinica(loja, styles), Spacer(1, 6)]
    story.append(Table(
        [[""]],
        colWidths=[17.8 * cm],
        rowHeights=[2],
        style=TableStyle([("LINEABOVE", (0, 0), (-1, 0), 1.2, VINHO)]),
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"Pedido de compra nº {pedido.numero}", styles["Title"]))

    ass_cli = pedido.assinaturas.filter(
        tipo=PedidoCompraAssinatura.TIPO_CLINICA, assinado=True,
    ).first()
    if ass_cli:
        prof_linhas = [
            "<b>Profissional responsável</b>",
            escape(ass_cli.nome_assinante or "—"),
        ]
        if ass_cli.cpf_assinante:
            prof_linhas.append(f"CPF: {escape(ass_cli.cpf_assinante)}")
        if ass_cli.conselho_display:
            prof_linhas.append(escape(ass_cli.conselho_display))
        story.append(Paragraph("<br/>".join(prof_linhas), styles["Meta"]))
        story.append(Spacer(1, 8))

    forn = pedido.fornecedor
    forn_linhas = [f"<b>Fornecedor:</b> {escape(forn.razao_social)}"]
    if forn.nome_fantasia:
        forn_linhas.append(f"Nome fantasia: {escape(forn.nome_fantasia)}")
    forn_linhas.append(f"CNPJ: {escape(forn.cnpj)}")
    end = " ".join(p for p in [forn.logradouro, forn.numero, forn.bairro, forn.municipio, forn.uf] if p)
    if end:
        forn_linhas.append(escape(end))
    story.append(Paragraph("<br/>".join(forn_linhas), styles["Meta"]))
    story.append(Spacer(1, 10))

    rows = [["Código", "Produto", "Un.", "Qtd", "Preço", "Subtotal"]]
    for item in pedido.itens.all():
        rows.append([
            item.codigo,
            Paragraph(escape(item.nome), styles["Small"]),
            item.unidade or "un",
            f"{item.quantidade:g}".replace(".", ","),
            _brl(item.preco),
            _brl(item.subtotal),
        ])
    rows.append(["", "", "", "", "Total", _brl(pedido.valor_total)])
    table = Table(rows, colWidths=[70, 190, 36, 40, 70, 75])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8eef1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), VINHO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f9fafb")),
    ]))
    story.append(table)

    if pedido.observacoes:
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>Observações:</b> {escape(pedido.observacoes)}", styles["Body"]))

    story.append(Spacer(1, 18))
    story.append(Paragraph("Assinaturas", styles["BoxTitle"]))
    story.append(Spacer(1, 6))

    def _bloco_assinatura(titulo: str, linhas: list[str]) -> list:
        return [
            Paragraph(f"<b>{escape(titulo)}</b>", styles["BoxTitle"]),
            Spacer(1, 4),
            *[Paragraph(escape(linha), styles["Small"]) for linha in linhas if linha],
        ]

    cli_linhas = []
    if ass_cli and ass_cli.assinado:
        cli_linhas.append(ass_cli.nome_assinante or "—")
        if ass_cli.cpf_assinante:
            cli_linhas.append(f"CPF: {ass_cli.cpf_assinante}")
        if ass_cli.conselho_display:
            cli_linhas.append(ass_cli.conselho_display)
        if ass_cli.assinado_em:
            cli_linhas.append(timezone.localtime(ass_cli.assinado_em).strftime("%d/%m/%Y %H:%M (GMT-3)"))
        cli_linhas.append(loja.get("nome") or "Clínica")
        if loja.get("cnpj"):
            cli_linhas.append(f"CNPJ: {loja['cnpj']}")
    else:
        cli_linhas.append("Pendente")

    ass_forn = pedido.assinaturas.filter(
        tipo=PedidoCompraAssinatura.TIPO_FORNECEDOR, assinado=True,
    ).first()
    forn_ass = []
    if ass_forn and ass_forn.assinado:
        forn_ass.append(ass_forn.nome_assinante or forn.razao_social)
        forn_ass.append(f"CNPJ: {forn.cnpj}")
        if ass_forn.assinado_em:
            forn_ass.append(timezone.localtime(ass_forn.assinado_em).strftime("%d/%m/%Y %H:%M (GMT-3)"))
    else:
        forn_ass.append("Pendente")

    esquerda = _bloco_assinatura("Clínica", cli_linhas)
    direita = _bloco_assinatura("Fornecedor", forn_ass)
    boxes = Table([[esquerda, direita]], colWidths=[8.8 * cm, 8.8 * cm])
    boxes.setStyle(TableStyle([
        ("BOX", (0, 0), (0, 0), 0.6, colors.HexColor("#e5e7eb")),
        ("BOX", (1, 0), (1, 0), 0.6, colors.HexColor("#e5e7eb")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fdfcfc")),
    ]))
    story.append(boxes)

    doc.build(story)
    return buf.getvalue()
