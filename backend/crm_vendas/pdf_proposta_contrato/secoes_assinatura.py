from ._pdf_base import *  # noqa: F401,F403
from .secoes_logo import *  # noqa: F401,F403
from .secoes_classicas import *  # noqa: F401,F403
from .secoes_identificacao import *  # noqa: F401,F403
from .secoes_investimento import *  # noqa: F401,F403
from .secoes_recursos import *  # noqa: F401,F403

def _build_secao_assinaturas(elements, documento, lead, vendedor, style, incluir_assinaturas=True, tipo_doc="proposta"):
    """Adiciona seção Assinaturas com dados digitais."""
    from reportlab.lib.units import cm
    from reportlab.platypus import Spacer
    proposta = tipo_doc == "proposta"
    elements.append(Spacer(1, 0.15 * cm if proposta else 0.35 * cm))
    if proposta:
        style = ParagraphStyle(
            "AssinaturaProposta",
            fontName=FONTE,
            fontSize=8,
            leading=10,
            textColor=COR_TEXTO,
        )
        section = ParagraphStyle(
            "SecAssinProposta",
            fontName=FONTE_NEGRITO,
            fontSize=11,
            textColor=COR_PROPOSTA,
            leading=13,
            spaceBefore=0,
            spaceAfter=2,
        )
        coluna = (A4[0] - 3.1 * cm) / 2
    else:
        section = ParagraphStyle("SecAssin", parent=style, fontSize=10, spaceBefore=2, spaceAfter=1)
        coluna = 8 * cm
    elements.append(Paragraph("Assinaturas", section))

    nome_vendedor = getattr(documento, "nome_vendedor_assinatura", None) or ""
    nome_cliente = getattr(documento, "nome_cliente_assinatura", None) or ""
    lead_email = getattr(lead, "email", "") or "" if lead else ""
    vendedor_email = getattr(vendedor, "email", "") or "" if vendedor else ""

    assinatura_vendedor = None
    assinatura_cliente = None
    if incluir_assinaturas:
        from ..models import AssinaturaDigital
        filtro = {"assinado": True}
        if tipo_doc == "proposta":
            filtro["proposta"] = documento
        else:
            filtro["contrato"] = documento
        for ass in AssinaturaDigital.objects.filter(**filtro).order_by("assinado_em"):
            if ass.tipo == "vendedor":
                assinatura_vendedor = ass
            elif ass.tipo == "cliente":
                assinatura_cliente = ass

    vendedor_nome_fmt = (nome_vendedor or _formatar_nome_usuario(vendedor)).strip().upper() or "—"
    cliente_nome_fmt = (nome_cliente or getattr(lead, "nome", "") or "—").strip().upper() or "—"

    vendedor_info = [f"Vendedor: {vendedor_nome_fmt}"]
    if vendedor_email:
        vendedor_info.append(f"<font size='8'>Email: {vendedor_email}</font>")
    if assinatura_vendedor:
        ts = _formatar_timestamp_local(assinatura_vendedor.assinado_em)
        vendedor_info.append(f'<font size="8">Assinado em: {ts}</font>')
        vendedor_info.append(f'<font size="8">IP: {assinatura_vendedor.ip_address}</font>')
        vendedor_info.append('<font size="8">Assinado digitalmente</font>')

    cliente_info = [f"Cliente: {cliente_nome_fmt}"]
    if lead_email:
        cliente_info.append(f"<font size='8'>Email: {lead_email}</font>")
    if assinatura_cliente:
        ts = _formatar_timestamp_local(assinatura_cliente.assinado_em)
        cliente_info.append(f'<font size="8">Assinado em: {ts}</font>')
        cliente_info.append(f'<font size="8">IP: {assinatura_cliente.ip_address}</font>')
        cliente_info.append('<font size="8">Assinado digitalmente</font>')

    assinatura_data = []
    max_rows = max(len(vendedor_info), len(cliente_info))
    for i in range(max_rows):
        v_text = Paragraph(vendedor_info[i], style) if i < len(vendedor_info) else ""
        c_text = Paragraph(cliente_info[i], style) if i < len(cliente_info) else ""
        assinatura_data.append([v_text, c_text])

    t = Table(assinatura_data, colWidths=[coluna, coluna])
    t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 4 if proposta else 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4 if proposta else 6),
        ("TOPPADDING", (0, 0), (-1, -1), 1 if proposta else 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0 if proposta else 1),
        ("BOX", (0, 0), (0, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("BOX", (1, 0), (1, -1), 0.5, colors.HexColor("#e5e7eb")),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.05 * cm if proposta else 0.1 * cm))

    # Mensagem de validade jurídica
    validade = ParagraphStyle(
        "Validade",
        parent=style,
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#666666"),
        alignment=TA_CENTER,
        spaceBefore=0 if proposta else 2,
    )
    elements.append(Paragraph(
        "Este documento possui validade jurídica e contém as assinaturas digitais de ambas as partes, "
        "com registro de data, hora e endereço IP.", validade))

    return assinatura_vendedor, assinatura_cliente


def _build_watermark_callback(logo_url, assinatura_vendedor, assinatura_cliente):
    """Prepara dados da marca d'água (logo transparente) para uso nas assinaturas.
    Retorna bytes PNG da imagem com transparência, ou None.
    """
    if not (assinatura_vendedor or assinatura_cliente) or not logo_url:
        return None
    try:
        conteudo = baixar_logo_pdf(logo_url)
        if not conteudo:
            return None
        pil_img = PILImage.open(BytesIO(conteudo)).convert("RGBA")
        alpha = pil_img.split()[3]
        alpha = alpha.point(lambda p: int(p * 0.25))
        pil_img.putalpha(alpha)
        out_buf = BytesIO()
        pil_img.save(out_buf, format="PNG")
        return out_buf.getvalue()
    except Exception:
        return None

__all__ = ['_build_secao_assinaturas', '_build_watermark_callback']
