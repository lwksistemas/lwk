from ._pdf_base import *  # noqa: F401,F403

def nome_item_documento(nome, prestadora_nome="") -> str:
    """Nome do item na proposta, sem repetir o tipo nem a marca da prestadora."""
    texto = (nome or "").strip()
    marcas = []
    bruto = (prestadora_nome or "").strip()
    if bruto:
        principal = bruto.split("—")[0].split("–")[0].strip()
        if principal:
            marcas.append(principal)
            primeira = principal.split()[0]
            if primeira and primeira not in marcas:
                marcas.append(primeira)
    for marca in marcas:
        if texto.upper().startswith(marca.upper()):
            resto = texto[len(marca):].lstrip(" —-–")
            if resto:
                return resto
    return texto or "Item"

def _recorte_logo(conteudo: bytes) -> bytes:
    """Tira a margem branca ou transparente para as duas marcas ficarem do mesmo tamanho."""
    imagem = PILImage.open(BytesIO(conteudo))
    imagem.load()
    if "A" in imagem.getbands():
        caixa = imagem.getchannel("A").point(lambda alpha: 255 if alpha > 12 else 0).getbbox()
    else:
        caixa = imagem.convert("RGB").convert("L").point(lambda valor: 0 if valor > 242 else 255).getbbox()
    if not caixa:
        return conteudo
    recorte = imagem.crop(caixa)
    if recorte.size[0] < 8 or recorte.size[1] < 8:
        return conteudo
    saida = BytesIO()
    recorte.save(saida, format="PNG")
    return saida.getvalue()


def _imagem_cabecalho(conteudo, max_w, max_h):
    """Monta a logo no tamanho do cabeçalho, sem esticar."""
    conteudo = _recorte_logo(conteudo)
    pil_img = PILImage.open(BytesIO(conteudo))
    largura_px, altura_px = pil_img.size
    if not largura_px or not altura_px:
        return None
    proporcao = altura_px / float(largura_px)
    largura = max_w
    altura = largura * proporcao
    if altura > max_h:
        altura = max_h
        largura = altura / proporcao
    imagem = Image(BytesIO(conteudo), width=largura, height=altura)
    imagem.hAlign = "CENTER"
    return imagem


def _par_mesma_altura(esquerda: bytes, direita: bytes, titulo: str, largura_util=None):
    """As duas logos saem com a mesma altura e deixam o título em uma linha."""
    esquerda = _recorte_logo(esquerda)
    direita = _recorte_logo(direita)
    proporcoes = []
    for conteudo in (esquerda, direita):
        largura_px, altura_px = PILImage.open(BytesIO(conteudo)).size
        proporcoes.append(largura_px / float(altura_px))
    util = largura_util if largura_util is not None else A4[0] - 4 * cm
    reserva_titulo = stringWidth(titulo, "Helvetica-Bold", 14) + 2.2 * cm
    altura = 1.6 * cm
    if altura * sum(proporcoes) > util - reserva_titulo:
        altura = (util - reserva_titulo) / sum(proporcoes)
    imagens = []
    for conteudo, proporcao in zip((esquerda, direita), proporcoes, strict=True):
        imagem = Image(BytesIO(conteudo), width=altura * proporcao, height=altura)
        imagem.hAlign = "CENTER"
        imagens.append(imagem)
    return imagens[0], imagens[1]


def _build_cabecalho(elements, logo_url, titulo, logo_direita_url=None, largura=None):
    """Logo principal à esquerda, título no centro e a logo do login à direita."""
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "HeaderTitle", parent=styles["Heading1"], fontSize=14,
        textColor=colors.HexColor("#0176d3"), alignment=TA_CENTER,
        spaceBefore=0, spaceAfter=0, leading=16,
    )
    esquerda = baixar_logo_pdf(logo_url) if logo_url else None
    direita_url = (logo_direita_url or "").strip()
    if direita_url and direita_url == (logo_url or "").strip():
        direita_url = ""
    direita = baixar_logo_pdf(direita_url) if direita_url else None
    if not esquerda and not direita:
        elements.append(Paragraph(titulo, title_style))
        return
    if esquerda and direita:
        try:
            util = largura if largura is not None else A4[0] - 4 * cm
            img_esquerda, img_direita = _par_mesma_altura(esquerda, direita, titulo, util)
            folga = 0.7 * cm
            coluna_esquerda = img_esquerda.drawWidth + folga
            coluna_direita = img_direita.drawWidth + folga
            meio = util - coluna_esquerda - coluna_direita
            tabela = Table(
                [[img_esquerda, Paragraph(titulo, title_style), img_direita]],
                colWidths=[coluna_esquerda, meio, coluna_direita],
            )
            tabela.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("ALIGN", (2, 0), (2, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (0, 0), 0),
                ("RIGHTPADDING", (0, 0), (0, 0), folga),
                ("LEFTPADDING", (1, 0), (1, 0), 4),
                ("RIGHTPADDING", (1, 0), (1, 0), 4),
                ("LEFTPADDING", (2, 0), (2, 0), folga),
                ("RIGHTPADDING", (2, 0), (2, 0), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            elements.append(tabela)
            return
        except Exception as exc:
            logger.warning("Erro ao montar as duas logos da proposta: %s", exc)
    unico = esquerda or direita
    title_style.alignment = TA_LEFT
    try:
        img = _imagem_cabecalho(unico, 6 * cm, 3 * cm)
        if not img:
            raise ValueError("Logo não disponível")
        tabela = Table([[img, Paragraph(titulo, title_style)]], colWidths=[6.5 * cm, None])
        tabela.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(tabela)
    except Exception as exc:
        logger.warning("Erro ao adicionar logo no PDF: %s", exc)
        title_style.alignment = TA_CENTER
        elements.append(Paragraph(titulo, title_style))



__all__ = ['nome_item_documento', '_recorte_logo', '_imagem_cabecalho', '_par_mesma_altura', '_build_cabecalho']
