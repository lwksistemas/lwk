"""Seções reutilizáveis do PDF de proposta/contrato."""
import logging
from io import BytesIO

import requests
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, Spacer, Table, TableStyle

from core.phone_utils import telefone_exibicao_brasileiro

from .formatters import (
    _formatar_endereco_lead,
    _formatar_nome_usuario,
    _formatar_timestamp_local,
    _formatar_valor,
    _html_to_paragraphs,
    _title_case_endereco,
)

logger = logging.getLogger(__name__)

def _build_cabecalho(elements, logo_url, titulo):
    """Cria cabeçalho com logo à esquerda e título à direita."""
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "HeaderTitle", parent=styles["Heading1"], fontSize=16,
        textColor=colors.HexColor("#0176d3"), alignment=TA_LEFT,
        spaceBefore=0, spaceAfter=0, leading=18,
    )
    if not logo_url:
        title_style.alignment = TA_CENTER
        elements.append(Paragraph(titulo, title_style))
        return
    try:
        response = requests.get(logo_url, timeout=5)
        if response.status_code != 200:
            raise ValueError("Logo não disponível")
        img_buffer = BytesIO(response.content)
        pil_img = PILImage.open(img_buffer)
        iw, ih = pil_img.size
        aspect = ih / float(iw)
        max_w, max_h = 6 * cm, 3 * cm
        width = min(max_w, iw)
        height = width * aspect
        if height > max_h:
            height = max_h
            width = height / aspect
        img_buffer.seek(0)
        img = Image(img_buffer, width=width, height=height)
        table = Table([[img, Paragraph(titulo, title_style)]], colWidths=[width + 0.5 * cm, None])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(table)
    except Exception as e:
        logger.warning(f"Erro ao adicionar logo no PDF: {e}")
        title_style.alignment = TA_CENTER
        elements.append(Paragraph(titulo, title_style))


def _build_secao_empresa(elements, loja_data, style):
    """Adiciona seção Dados da Empresa."""
    from reportlab.lib.units import cm
    from reportlab.platypus import Spacer
    elements.append(Spacer(1, 0.2 * cm))
    section = ParagraphStyle("SecEmpresa", parent=style, fontSize=10, spaceBefore=2, spaceAfter=1)
    elements.append(Paragraph("<b>Dados da Empresa</b>", section))
    linhas = [f"<b>Nome:</b> {loja_data.get('nome') or '—'}"]
    if loja_data.get("endereco"):
        linhas.append(f"<b>Endereço:</b> {_title_case_endereco(loja_data['endereco'])}")
    if loja_data.get("cpf_cnpj"):
        linhas.append(f"<b>CPF/CNPJ:</b> {loja_data['cpf_cnpj']}")
    if loja_data.get("telefone"):
        tel_fmt = telefone_exibicao_brasileiro(loja_data["telefone"]) or loja_data["telefone"].strip()
        linhas.append(f"<b>Telefone:</b> {tel_fmt}")
    if loja_data.get("admin_nome"):
        linhas.append(f"<b>Responsável:</b> {loja_data['admin_nome']}")
    if loja_data.get("admin_email"):
        linhas.append(f"<b>Email:</b> {loja_data['admin_email']}")
    for ln in linhas:
        elements.append(Paragraph(ln, style))


def _build_secao_cliente(elements, lead, style):
    """Adiciona seção Dados do Cliente."""
    from reportlab.lib.units import cm
    from reportlab.platypus import Spacer
    elements.append(Spacer(1, 0.2 * cm))
    section = ParagraphStyle("SecCliente", parent=style, fontSize=10, spaceBefore=2, spaceAfter=1)
    elements.append(Paragraph("<b>Dados do Cliente</b>", section))
    conta = getattr(lead, "conta", None)
    if conta:
        elements.append(Paragraph(f"<b>Nome:</b> {lead.nome}", style))
        empresa_nome = conta.razao_social or conta.nome or ""
        if empresa_nome:
            elements.append(Paragraph(f"<b>Empresa:</b> {empresa_nome}", style))
    else:
        elements.append(Paragraph(f"<b>Nome:</b> {lead.nome}", style))
    if getattr(lead, "cpf_cnpj", ""):
        elements.append(Paragraph(f"<b>CPF/CNPJ:</b> {lead.cpf_cnpj}", style))
    if getattr(lead, "telefone", ""):
        tel_fmt = telefone_exibicao_brasileiro(lead.telefone) or (lead.telefone or "").strip()
        elements.append(Paragraph(f"<b>Telefone:</b> {tel_fmt}", style))
    if getattr(lead, "email", ""):
        elements.append(Paragraph(f"<b>Email:</b> {lead.email}", style))
    elements.append(Paragraph(f"<b>Endereço:</b> {_formatar_endereco_lead(lead)}", style))


def _build_secao_produtos(elements, oportunidade, style, incluir_recorrencia=True):
    """Adiciona seção Produtos e Serviços."""
    from reportlab.lib.units import cm
    from reportlab.platypus import Spacer
    elements.append(Spacer(1, 0.2 * cm))
    section = ParagraphStyle("SecProd", parent=style, fontSize=10, spaceBefore=2, spaceAfter=1)
    elements.append(Paragraph("<b>Produtos e Serviços da Oportunidade</b>", section))
    itens = list(oportunidade.itens.select_related("produto_servico").all()) if oportunidade else []
    if not itens:
        elements.append(Paragraph("Nenhum item cadastrado.", style))
        return 0, 0
    if incluir_recorrencia:
        table_data = [["Item", "Recorrência", "Qtd", "Preço Unit.", "Subtotal"]]
    else:
        table_data = [["Item", "Qtd", "Preço Unit.", "Subtotal"]]
    valor_unico = 0
    valor_mensal = 0
    valor_trimestral = 0
    valor_anual = 0
    for item in itens:
        ps = item.produto_servico
        tipo_ps = ps.get_tipo_display() if hasattr(ps, "get_tipo_display") else getattr(ps, "tipo", "")
        nome = f"{tipo_ps}: {ps.nome}" if tipo_ps else ps.nome
        recorrencia = getattr(ps, "recorrencia", "unico") or "unico"
        recorrencia_label = {"unico": "Único", "mensal": "Mensal", "trimestral": "Trimestral", "anual": "Anual"}.get(recorrencia, recorrencia)
        qtd = str(item.quantidade) if item.quantidade is not None else "1"
        preco = _formatar_valor(item.preco_unitario)
        sub = item.quantidade * item.preco_unitario if item.quantidade and item.preco_unitario else 0
        subtotal = _formatar_valor(sub)
        if incluir_recorrencia:
            table_data.append([nome, recorrencia_label, qtd, preco, subtotal])
        else:
            table_data.append([nome, qtd, preco, subtotal])
        if recorrencia == "unico":
            valor_unico += float(sub)
        elif recorrencia == "mensal":
            valor_mensal += float(sub)
        elif recorrencia == "trimestral":
            valor_trimestral += float(sub)
        elif recorrencia == "anual":
            valor_anual += float(sub)
    if incluir_recorrencia:
        col_widths = [None, 60, 35, 65, 65]
    else:
        col_widths = [None, 40, 70, 70]
    t = Table(table_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e3f3ff")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    t.hAlign = "LEFT"
    elements.append(t)
    return valor_unico, valor_mensal, valor_trimestral, valor_anual


def _build_secao_desconto(elements, documento, style):
    """Adiciona resumo financeiro com tabela visual."""
    valor_total = documento.valor_total
    desconto_valor = getattr(documento, "desconto_valor", None) or 0
    has_desconto = desconto_valor and float(desconto_valor) > 0

    # Buscar valores de adesão/mensal/anual se disponíveis nos itens
    oportunidade = getattr(documento, "oportunidade", None)
    valor_unico = 0
    valor_mensal = 0
    valor_trimestral = 0
    valor_anual = 0
    if oportunidade:
        try:
            for item in oportunidade.itens.select_related("produto_servico").all():
                ps = item.produto_servico
                recorrencia = getattr(ps, "recorrencia", "unico") or "unico"
                sub = float(item.quantidade * item.preco_unitario) if item.quantidade and item.preco_unitario else 0
                if recorrencia == "unico":
                    valor_unico += sub
                elif recorrencia == "mensal":
                    valor_mensal += sub
                elif recorrencia == "trimestral":
                    valor_trimestral += sub
                elif recorrencia == "anual":
                    valor_anual += sub
        except Exception:
            pass

    # Montar tabela de resumo financeiro
    resumo_data = []
    if valor_unico > 0:
        resumo_data.append(["Adesão/Implantação:", _formatar_valor(valor_unico)])
    if valor_mensal > 0:
        resumo_data.append(["Valor Mensal:", f"{_formatar_valor(valor_mensal)}/mês"])
    if valor_trimestral > 0:
        resumo_data.append(["Valor Trimestral:", f"{_formatar_valor(valor_trimestral)}/trimestre"])
    if valor_anual > 0:
        resumo_data.append(["Valor Anual:", f"{_formatar_valor(valor_anual)}/ano"])
    resumo_data.append(["Valor Total:", _formatar_valor(valor_total)])
    if has_desconto:
        desconto_tipo = getattr(documento, "desconto_tipo", "percentual")
        if desconto_tipo == "percentual":
            resumo_data.append(["Desconto:", f"{desconto_valor}%"])
        else:
            resumo_data.append(["Desconto:", _formatar_valor(desconto_valor)])
        valor_final = getattr(documento, "valor_com_desconto", valor_total)
        resumo_data.append(["Valor com Desconto:", _formatar_valor(valor_final)])

    t = Table(resumo_data, colWidths=[5 * cm, 5 * cm])
    style_cmds = [
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f9ff")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#0176d3")),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#e5e7eb")),
    ]
    # Destacar última linha (valor final)
    last = len(resumo_data) - 1
    style_cmds.append(("FONTNAME", (0, last), (-1, last), "Helvetica-Bold"))
    style_cmds.append(("FONTSIZE", (0, last), (-1, last), 10))
    style_cmds.append(("BACKGROUND", (0, last), (-1, last), colors.HexColor("#e0f2fe")))
    style_cmds.append(("TEXTCOLOR", (1, last), (1, last), colors.HexColor("#0176d3")))
    t.setStyle(TableStyle(style_cmds))
    t.hAlign = "LEFT"
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(t)
    elements.append(Spacer(1, 0.2 * cm))


def _build_secao_conteudo(elements, conteudo, style):
    """Adiciona seção Conteúdo."""
    section = ParagraphStyle("SecConteudo", parent=style, fontSize=10, spaceBefore=2, spaceAfter=1)
    elements.append(Paragraph("<b>Conteúdo</b>", section))
    styles = getSampleStyleSheet()
    conteudo_style = ParagraphStyle(
        "ConteudoJustificado",
        parent=styles["Normal"],
        fontSize=style.fontSize if hasattr(style, "fontSize") else 9,
        leading=style.leading if hasattr(style, "leading") else 11,
        alignment=TA_JUSTIFY,
        spaceBefore=2,
        spaceAfter=4,
    )
    for p in _html_to_paragraphs(conteudo)[:100]:
        if p == "":
            elements.append(Spacer(1, 0.2 * cm))
        else:
            elements.append(Paragraph(p[:500], conteudo_style))


def _build_secao_assinaturas(elements, documento, lead, vendedor, style, incluir_assinaturas=True, tipo_doc="proposta"):
    """Adiciona seção Assinaturas com dados digitais."""
    from reportlab.lib.units import cm
    from reportlab.platypus import Spacer
    elements.append(Spacer(1, 0.2 * cm))
    section = ParagraphStyle("SecAssin", parent=style, fontSize=10, spaceBefore=2, spaceAfter=1)
    elements.append(Paragraph("<b>Assinaturas</b>", section))

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

    t = Table(assinatura_data, colWidths=[8 * cm, 8 * cm])
    t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("BOX", (0, 0), (0, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("BOX", (1, 0), (1, -1), 0.5, colors.HexColor("#e5e7eb")),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.1 * cm))

    # Mensagem de validade jurídica
    validade = ParagraphStyle("Validade", parent=style, fontSize=7,
                              textColor=colors.HexColor("#666666"), alignment=TA_CENTER, spaceBefore=2)
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
        resp = requests.get(logo_url, timeout=5)
        if resp.status_code != 200:
            return None
        pil_img = PILImage.open(BytesIO(resp.content)).convert("RGBA")
        alpha = pil_img.split()[3]
        alpha = alpha.point(lambda p: int(p * 0.25))
        pil_img.putalpha(alpha)
        out_buf = BytesIO()
        pil_img.save(out_buf, format="PNG")
        return out_buf.getvalue()
    except Exception:
        return None
