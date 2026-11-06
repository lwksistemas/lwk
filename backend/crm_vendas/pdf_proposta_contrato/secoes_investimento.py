from ._pdf_base import *  # noqa: F401,F403
from .secoes_logo import *  # noqa: F401,F403
from .secoes_classicas import *  # noqa: F401,F403
from .secoes_identificacao import *  # noqa: F401,F403

def _itens_oportunidade(oportunidade):
    if oportunidade is None:
        return []
    relacao = getattr(oportunidade, "itens", None)
    if relacao is None:
        return []
    if hasattr(relacao, "select_related"):
        return list(relacao.select_related("produto_servico").all())
    return list(relacao)


def _build_tabela_investimento_visual(elements, oportunidade):
    """Tabela Serviço, Quantidade, Cobrança e Valor. O valor já multiplica a quantidade."""
    _titulo_numerado(elements, 2, "Investimento")
    itens = _itens_oportunidade(oportunidade)
    if not itens:
        elements.append(Paragraph("Nenhum item cadastrado.", _estilo_corpo_proposta()))
        return 0, 0, 0, 0, 0
    prestadora = getattr(oportunidade, "empresa_prestadora", None)
    marca = getattr(prestadora, "nome", "") if prestadora is not None else ""
    header_style = ParagraphStyle(
        "HeadInvestimento",
        fontName=FONTE_NEGRITO,
        fontSize=8,
        textColor=colors.white,
        leading=10,
    )
    header_centro = ParagraphStyle("HeadInvestimentoCentro", parent=header_style, alignment=TA_CENTER)
    header_direita = ParagraphStyle("HeadInvestimentoDireita", parent=header_style, alignment=TA_RIGHT)
    nome_style = ParagraphStyle("NomeInvestimento", fontName=FONTE, fontSize=8, leading=10, textColor=COR_TEXTO)
    celula = ParagraphStyle("CelulaInvestimento", fontName=FONTE, fontSize=8, leading=10, textColor=COR_TEXTO, alignment=TA_CENTER)
    valor_style = ParagraphStyle("ValorInvestimento", fontName=FONTE, fontSize=8, leading=10, textColor=COR_TEXTO, alignment=TA_RIGHT)
    mostra_unitario = _mostra_valor_unitario(itens)
    cabecalhos = [
        Paragraph("Serviço", header_style),
        Paragraph("Qtd", header_centro),
        Paragraph("Investimento", header_centro),
    ]
    if mostra_unitario:
        cabecalhos.append(Paragraph("Valor un.", header_direita))
        cabecalhos.append(Paragraph("Total", header_direita))
    else:
        cabecalhos.append(Paragraph("Valor", header_direita))
    table_data = [cabecalhos]
    totais = {"unico": 0, "mensal": 0, "trimestral": 0, "semestral": 0, "anual": 0}
    rotulos = {
        "unico": "Única",
        "mensal": "Mensal",
        "trimestral": "Trimestral",
        "semestral": "Semestral",
        "anual": "Anual",
    }
    for item in itens:
        produto = getattr(item, "produto_servico", None)
        nome = nome_item_documento(getattr(produto, "nome", ""), marca)
        quantidade = getattr(item, "quantidade", 1)
        recorrencia = getattr(produto, "recorrencia", "unico") or "unico"
        subtotal = _subtotal_item(item)
        totais[recorrencia] = totais.get(recorrencia, 0) + subtotal
        linha = [
            Paragraph(escape(nome), nome_style),
            Paragraph(_quantidade_texto(quantidade), celula),
            Paragraph(rotulos.get(recorrencia, recorrencia), celula),
        ]
        if mostra_unitario:
            linha.append(Paragraph(_formatar_valor(_preco_unitario_item(item)), valor_style))
        linha.append(Paragraph(_formatar_valor(subtotal), valor_style))
        table_data.append(linha)
    largura = A4[0] - 3.1 * cm
    if mostra_unitario:
        colunas = [largura - 11.2 * cm, 1.6 * cm, 3.4 * cm, 3.1 * cm, 3.1 * cm]
        alinhamento_valor = ("ALIGN", (3, 0), (4, -1), "RIGHT")
    else:
        colunas = [largura - 8.2 * cm, 1.8 * cm, 3.2 * cm, 3.2 * cm]
        alinhamento_valor = ("ALIGN", (3, 0), (3, -1), "RIGHT")
    tabela = Table(table_data, colWidths=colunas)
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COR_PROPOSTA),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COR_FAIXA]),
        ("ALIGN", (1, 0), (2, -1), "CENTER"),
        alinhamento_valor,
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    tabela.hAlign = "LEFT"
    elements.append(tabela)
    return totais["unico"], totais["mensal"], totais["trimestral"], totais["semestral"], totais["anual"]


def _quantidade_numero(quantidade) -> float:
    if quantidade is None or quantidade == "":
        return 1.0
    try:
        return float(quantidade)
    except (TypeError, ValueError):
        return 1.0


def _mostra_valor_unitario(itens) -> bool:
    """A coluna do valor por unidade só entra quando alguma quantidade passa de 1."""
    return any(_quantidade_numero(getattr(item, "quantidade", 1)) > 1 for item in itens or [])


def _quantidade_texto(quantidade) -> str:
    numero = _quantidade_numero(quantidade)
    if numero.is_integer():
        return str(int(numero))
    return f"{numero:.2f}".replace(".", ",")


def _preco_unitario_item(item) -> float:
    preco = getattr(item, "preco_unitario", 0) or 0
    try:
        return float(preco)
    except (TypeError, ValueError):
        return 0


def _subtotal_item(item) -> float:
    quantidade = getattr(item, "quantidade", 0) or 0
    preco = getattr(item, "preco_unitario", 0) or 0
    try:
        return float(quantidade) * float(preco)
    except (TypeError, ValueError):
        return 0


def _build_resumo_visual(elements, documento, totais):
    """Pagamento inicial, o que ele inclui e as cobranças seguintes, em linhas."""
    from .formatters import linhas_resumo_investimento, texto_resumo_visual

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
    blocos = texto_resumo_visual(linhas, frase)
    if not blocos:
        return
    elements.append(Spacer(1, 0.35 * cm))
    forte = ParagraphStyle(
        "ResumoForte",
        fontName=FONTE_NEGRITO,
        fontSize=15,
        textColor=COR_PROPOSTA,
        leading=18,
        spaceBefore=2,
        spaceAfter=1,
    )
    seguinte = ParagraphStyle(
        "ResumoSeguinte",
        fontName=FONTE_NEGRITO,
        fontSize=12,
        textColor=COR_PROPOSTA,
        leading=15,
        spaceBefore=4,
        spaceAfter=1,
    )
    nota = ParagraphStyle(
        "ResumoNota",
        fontName=FONTE,
        fontSize=9,
        textColor=COR_TEXTO,
        leading=13,
        spaceBefore=1,
        spaceAfter=1,
    )
    primeiro_negrito = True
    for texto, negrito in blocos:
        if not negrito:
            elements.append(Paragraph(escape(texto), nota))
            continue
        elements.append(Paragraph(escape(texto), forte if primeiro_negrito else seguinte))
        primeiro_negrito = False


def _build_pagamento_inicial_visual(elements, titulo, linhas, fonte=None, fonte_negrito=None, tamanho=9):
    """Texto da primeira folha, abaixo de Mensalidades seguintes."""
    linhas = list(linhas or [])
    if not titulo and not any(_markup_linha(linha) for linha in linhas):
        return
    elements.append(Spacer(1, 0.22 * cm))
    titulo_tamanho = min(tamanho + 2, 16)
    titulo = linguagem_investimento(titulo or "")
    if titulo:
        elements.append(Paragraph(f"<b>{escape(titulo)}</b>", ParagraphStyle(
            f"TituloPagamentoInicial{fonte_negrito or FONTE_NEGRITO}{titulo_tamanho}",
            fontName=fonte_negrito or FONTE_NEGRITO,
            fontSize=titulo_tamanho,
            textColor=COR_PROPOSTA,
            leading=titulo_tamanho + 3,
            spaceBefore=10,
            spaceAfter=4,
        )))
    corpo = _estilo_corpo_proposta(fonte, tamanho)
    for linha in linhas:
        if not " ".join((linha or "").split()):
            elements.append(Spacer(1, 0.35 * cm))
            continue
        markup = _markup_linha(linha)
        if markup:
            elements.append(Paragraph(markup, corpo))


def _descricoes_incluidas(oportunidade):
    from .formatters import descricao_util_na_proposta

    vistos = set()
    blocos = []
    prestadora = getattr(oportunidade, "empresa_prestadora", None) if oportunidade is not None else None
    marca = getattr(prestadora, "nome", "") if prestadora is not None else ""
    for item in _itens_oportunidade(oportunidade):
        produto = getattr(item, "produto_servico", None)
        recorrencia = getattr(produto, "recorrencia", "unico") or "unico"
        if recorrencia == "unico":
            continue
        texto = " ".join((getattr(produto, "descricao", None) or "").split())
        if not descricao_util_na_proposta(texto) or texto in vistos:
            continue
        vistos.add(texto)
        nome = nome_item_documento(getattr(produto, "nome", ""), marca)
        blocos.append((nome, texto))
    return blocos


def _linhas_implantacao(oportunidade):
    from .formatters import descricao_util_na_proposta

    prestadora = getattr(oportunidade, "empresa_prestadora", None) if oportunidade is not None else None
    marca = getattr(prestadora, "nome", "") if prestadora is not None else ""
    linhas = []
    for item in _itens_oportunidade(oportunidade):
        produto = getattr(item, "produto_servico", None)
        recorrencia = getattr(produto, "recorrencia", "unico") or "unico"
        if recorrencia != "unico":
            continue
        nome = nome_item_documento(getattr(produto, "nome", ""), marca)
        valor = _formatar_valor(_subtotal_item(item))
        texto = " ".join((getattr(produto, "descricao", None) or "").split())
        if descricao_util_na_proposta(texto):
            linhas.append(f"{nome} — {valor}: {texto}")
        else:
            linhas.append(f"{nome} — {valor}")
    return linhas



__all__ = ['_itens_oportunidade', '_build_tabela_investimento_visual', '_quantidade_numero', '_mostra_valor_unitario', '_quantidade_texto', '_preco_unitario_item', '_subtotal_item', '_build_resumo_visual', '_build_pagamento_inicial_visual', '_descricoes_incluidas', '_linhas_implantacao']
