from ._pdf_base import *  # noqa: F401,F403
from .secoes_logo import *  # noqa: F401,F403

def _build_secao_empresa(elements, loja_data, style, titulo="Dados da Empresa"):
    """Adiciona seção Dados da Empresa."""
    from reportlab.lib.units import cm
    from reportlab.platypus import Spacer
    elements.append(Spacer(1, 0.2 * cm))
    section = ParagraphStyle("SecEmpresa", parent=style, fontSize=10, spaceBefore=2, spaceAfter=1)
    elements.append(Paragraph(f"<b>{escape(titulo)}</b>", section))
    linhas = [f"<b>Nome:</b> {loja_data.get('nome') or '—'}"]
    if loja_data.get("endereco"):
        linhas.append(f"<b>Endereço:</b> {_title_case_endereco(loja_data['endereco'])}")
    if loja_data.get("cpf_cnpj"):
        from .secoes_identificacao import _documento_exibicao

        linhas.append(f"<b>CPF/CNPJ:</b> {_documento_exibicao(loja_data['cpf_cnpj'])}")
    if loja_data.get("telefone"):
        tel_fmt = telefone_exibicao_brasileiro(loja_data["telefone"]) or loja_data["telefone"].strip()
        linhas.append(f"<b>Telefone:</b> {tel_fmt}")
    if loja_data.get("admin_nome"):
        linhas.append(f"<b>Responsável:</b> {loja_data['admin_nome']}")
    if loja_data.get("admin_email"):
        linhas.append(f"<b>Email:</b> {loja_data['admin_email']}")
    for ln in linhas:
        elements.append(Paragraph(ln, style))


def _build_secao_cliente(elements, lead, style, titulo="Dados do Cliente"):
    """Adiciona seção Dados do Cliente."""
    from reportlab.lib.units import cm
    from reportlab.platypus import Spacer
    elements.append(Spacer(1, 0.2 * cm))
    section = ParagraphStyle("SecCliente", parent=style, fontSize=10, spaceBefore=2, spaceAfter=1)
    elements.append(Paragraph(f"<b>{escape(titulo)}</b>", section))
    conta = getattr(lead, "conta", None)
    if conta:
        elements.append(Paragraph(f"<b>Nome:</b> {lead.nome}", style))
        empresa_nome = conta.razao_social or conta.nome or ""
        if empresa_nome:
            elements.append(Paragraph(f"<b>Empresa:</b> {empresa_nome}", style))
    else:
        elements.append(Paragraph(f"<b>Nome:</b> {lead.nome}", style))
    if getattr(lead, "cpf_cnpj", ""):
        from .secoes_identificacao import _documento_exibicao

        elements.append(Paragraph(f"<b>CPF/CNPJ:</b> {_documento_exibicao(lead.cpf_cnpj)}", style))
    if getattr(lead, "telefone", ""):
        tel_fmt = telefone_exibicao_brasileiro(lead.telefone) or (lead.telefone or "").strip()
        elements.append(Paragraph(f"<b>Telefone:</b> {tel_fmt}", style))
    if getattr(lead, "email", ""):
        elements.append(Paragraph(f"<b>Email:</b> {lead.email}", style))
    elements.append(Paragraph(f"<b>Endereço:</b> {_formatar_endereco_lead(lead)}", style))


def _build_secao_produtos(elements, oportunidade, style, incluir_recorrencia=True, titulo="Produtos e Serviços da Oportunidade"):
    """Adiciona seção Produtos e Serviços."""
    from reportlab.lib.units import cm
    from reportlab.platypus import Spacer
    elements.append(Spacer(1, 0.2 * cm))
    section = ParagraphStyle("SecProd", parent=style, fontSize=10, spaceBefore=2, spaceAfter=1)
    elements.append(Paragraph(f"<b>{escape(titulo)}</b>", section))
    itens = list(oportunidade.itens.select_related("produto_servico").all()) if oportunidade else []
    if not itens:
        elements.append(Paragraph("Nenhum item cadastrado.", style))
        return 0, 0, 0, 0, 0
    nome_style = ParagraphStyle("ItemNomePdf", fontName="Helvetica", fontSize=8, leading=10)
    if incluir_recorrencia:
        table_data = [["Item", "Recorrência", "Qtd", "Preço Unit.", "Subtotal"]]
    else:
        table_data = [["Item", "Qtd", "Preço Unit.", "Subtotal"]]
    valor_unico = 0
    valor_mensal = 0
    valor_trimestral = 0
    valor_semestral = 0
    valor_anual = 0
    for item in itens:
        ps = item.produto_servico
        prestadora = getattr(oportunidade, "empresa_prestadora", None)
        marca = getattr(prestadora, "nome", "") if prestadora is not None else ""
        nome = Paragraph(escape(nome_item_documento(getattr(ps, "nome", ""), marca)), nome_style)
        recorrencia = getattr(ps, "recorrencia", "unico") or "unico"
        recorrencia_label = {
            "unico": "Único",
            "mensal": "Mensal",
            "trimestral": "Trimestral",
            "semestral": "Semestral",
            "anual": "Anual",
        }.get(recorrencia, recorrencia)
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
        elif recorrencia == "semestral":
            valor_semestral += float(sub)
        elif recorrencia == "anual":
            valor_anual += float(sub)
    largura = A4[0] - 4 * cm
    if incluir_recorrencia:
        col_widths = [largura - 230, 70, 30, 65, 65]
    else:
        col_widths = [largura - 175, 40, 70, 65]
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
    return valor_unico, valor_mensal, valor_trimestral, valor_semestral, valor_anual


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
    valor_semestral = 0
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
                elif recorrencia == "semestral":
                    valor_semestral += sub
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
    if valor_semestral > 0:
        resumo_data.append(["Valor Semestral:", f"{_formatar_valor(valor_semestral)}/semestre"])
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


def _build_resumo_investimento(elements, documento, totais, style):
    """Pagamento inicial e cobranças seguintes da proposta."""
    from .formatters import linhas_resumo_investimento

    unico, mensal, trimestral, semestral, anual = totais
    linhas, frase = linhas_resumo_investimento(
        unico=unico,
        mensal=mensal,
        trimestral=trimestral,
        semestral=semestral,
        anual=anual,
        valor_total=getattr(documento, "valor_total", None),
        desconto_valor=getattr(documento, "desconto_valor", None) or 0,
        desconto_tipo=getattr(documento, "desconto_tipo", "percentual") or "percentual",
        valor_com_desconto=getattr(documento, "valor_com_desconto", None),
    )
    if not linhas:
        return
    resumo_data = [[rotulo, valor] for rotulo, valor in linhas]
    t = Table(resumo_data, colWidths=[5.4 * cm, 5 * cm])
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
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0f2fe")),
    ]
    t.setStyle(TableStyle(style_cmds))
    t.hAlign = "LEFT"
    elements.append(Spacer(1, 0.15 * cm))
    elements.append(t)
    if frase:
        nota = ParagraphStyle("NotaInvestimento", parent=style, fontSize=8, leading=11, spaceBefore=3, spaceAfter=2)
        elements.append(Paragraph(escape(frase), nota))
    elements.append(Spacer(1, 0.15 * cm))


def _build_secao_incluidos(elements, oportunidade, style):
    """Descrição cadastrada de cada serviço, fora do texto do template."""
    from .formatters import descricao_util_na_proposta

    if oportunidade is None:
        return
    relacao = getattr(oportunidade, "itens", None)
    if relacao is None:
        return
    itens = relacao.select_related("produto_servico").all() if hasattr(relacao, "select_related") else relacao
    prestadora = getattr(oportunidade, "empresa_prestadora", None)
    marca = getattr(prestadora, "nome", "") if prestadora is not None else ""
    vistos = set()
    blocos = []
    for item in itens:
        produto = getattr(item, "produto_servico", None)
        texto = " ".join((getattr(produto, "descricao", None) or "").split())
        if not descricao_util_na_proposta(texto) or texto in vistos:
            continue
        vistos.add(texto)
        nome = nome_item_documento(getattr(produto, "nome", ""), marca)
        blocos.append((nome, texto))
    if not blocos:
        return
    section = ParagraphStyle("SecIncluidos", parent=style, fontSize=10, spaceBefore=4, spaceAfter=2)
    elements.append(Paragraph("<b>O que está incluído</b>", section))
    nome_style = ParagraphStyle("IncluidoNome", parent=style, fontName="Helvetica-Bold", fontSize=9, spaceBefore=3, spaceAfter=1)
    texto_style = ParagraphStyle(
        "IncluidoTexto",
        parent=style,
        fontSize=9,
        leading=12,
        alignment=TA_JUSTIFY,
        spaceBefore=0,
        spaceAfter=3,
    )
    for nome, texto in blocos:
        elements.append(Paragraph(escape(nome), nome_style))
        elements.append(Paragraph(escape(texto), texto_style))


def _build_secao_condicoes(elements, paragrafos, style):
    """Texto do template da prestadora: condições, prazo e pagamento."""
    if not paragrafos:
        return
    section = ParagraphStyle("SecCondicoes", parent=style, fontSize=10, spaceBefore=4, spaceAfter=2)
    elements.append(Paragraph("<b>Condições e pagamento</b>", section))
    conteudo_style = ParagraphStyle(
        "CondicoesTexto",
        parent=style,
        fontSize=9,
        leading=12,
        alignment=TA_JUSTIFY,
        spaceBefore=2,
        spaceAfter=4,
    )
    for paragrafo in paragrafos:
        if paragrafo == "":
            elements.append(Spacer(1, 0.15 * cm))
        else:
            elements.append(Paragraph(escape(paragrafo), conteudo_style))


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
            elements.append(Paragraph(escape(p), conteudo_style))


COR_PROPOSTA = colors.HexColor("#1B365D")
COR_TEXTO = colors.HexColor("#1F2937")
COR_FAIXA = colors.HexColor("#F4F7FB")

__all__ = [
    "_build_secao_empresa",
    "_build_secao_cliente",
    "_build_secao_produtos",
    "_build_secao_desconto",
    "_build_resumo_investimento",
    "_build_secao_incluidos",
    "_build_secao_condicoes",
    "_build_secao_conteudo",
    "COR_PROPOSTA",
    "COR_TEXTO",
    "COR_FAIXA",
]
