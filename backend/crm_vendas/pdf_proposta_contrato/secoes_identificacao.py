from ._pdf_base import *  # noqa: F401,F403
from .secoes_logo import *  # noqa: F401,F403
from .secoes_classicas import *  # noqa: F401,F403


def _par_logos(url_esquerda, url_direita):
    """Baixa cada logo uma vez. A segunda folha reutiliza os mesmos arquivos."""
    esquerda = baixar_logo_pdf(url_esquerda) if url_esquerda else None
    direita_url = (url_direita or "").strip()
    if direita_url and direita_url == (url_esquerda or "").strip():
        direita_url = ""
    direita = baixar_logo_pdf(direita_url) if direita_url else None
    return esquerda, direita


def _build_faixa_logos(elements, esquerda, direita):
    """Logos nas laterais, sem título no meio."""
    if not esquerda and not direita:
        return
    altura_max = 1.9 * cm
    util = A4[0] - 3.1 * cm

    def montar(conteudo):
        recorte = _recorte_logo(conteudo)
        largura_px, altura_px = PILImage.open(BytesIO(recorte)).size
        if not largura_px or not altura_px:
            return None
        proporcao = largura_px / float(altura_px)
        largura = min(altura_max * proporcao, util * 0.46)
        return Image(BytesIO(recorte), width=largura, height=largura / proporcao)

    img_esquerda = montar(esquerda) if esquerda else None
    img_direita = montar(direita) if direita else None
    if img_esquerda and img_direita:
        meio = max(util - img_esquerda.drawWidth - img_direita.drawWidth, 0.3 * cm)
        tabela = Table(
            [[img_esquerda, "", img_direita]],
            colWidths=[img_esquerda.drawWidth, meio, img_direita.drawWidth],
        )
        tabela.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, 0), "LEFT"),
            ("ALIGN", (2, 0), (2, 0), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(tabela)
    else:
        imagem = img_esquerda or img_direita
        imagem.hAlign = "LEFT" if img_esquerda else "RIGHT"
        elements.append(imagem)
    elements.append(Spacer(1, 0.15 * cm))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=COR_PROPOSTA, spaceBefore=1, spaceAfter=8))


def _estilo_titulo_proposta():
    return ParagraphStyle(
        "TituloPropostaVisual",
        fontName=FONTE_NEGRITO,
        fontSize=20,
        textColor=COR_PROPOSTA,
        alignment=TA_LEFT,
        leading=24,
        spaceBefore=2,
        spaceAfter=2,
    )


def _estilo_titulo_recursos():
    return ParagraphStyle(
        "TituloRecursosVisual",
        fontName=FONTE_NEGRITO,
        fontSize=18,
        textColor=COR_PROPOSTA,
        alignment=TA_LEFT,
        leading=22,
        spaceBefore=2,
        spaceAfter=8,
    )


def _estilo_subtitulo_proposta():
    return ParagraphStyle(
        "SubtituloPropostaVisual",
        fontName=FONTE,
        fontSize=10,
        textColor=colors.HexColor("#4B5563"),
        leading=13,
        spaceBefore=4,
        spaceAfter=8,
    )


def _estilo_secao_proposta(fonte=None, tamanho=11):
    nome = fonte or FONTE_NEGRITO
    return ParagraphStyle(
        f"SecaoProposta{nome}{tamanho}",
        fontName=nome,
        fontSize=tamanho,
        textColor=COR_PROPOSTA,
        leading=tamanho + 3,
        spaceBefore=0,
        spaceAfter=4,
    )


def _estilo_corpo_proposta(fonte=None, tamanho=9):
    nome = fonte or FONTE
    return ParagraphStyle(
        f"CorpoProposta{nome}{tamanho}",
        fontName=nome,
        fontSize=tamanho,
        textColor=COR_TEXTO,
        leading=tamanho + 4,
        spaceBefore=0,
        spaceAfter=0,
    )


def _titulo_numerado(elements, numero, titulo, estilo=None):
    elements.append(Paragraph(f"{numero:02d}  {escape(titulo)}", estilo or _estilo_secao_proposta()))


def _markup_linha(texto: str) -> str:
    bruto = linguagem_investimento(" ".join((texto or "").split()))
    if not bruto:
        return ""
    if bruto.lower().startswith("banco ") or "agência" in bruto.lower() or "agencia" in bruto.lower():
        return f"<b>{escape(bruto)}</b>"
    if ":" in bruto and "•" not in bruto.split(":", 1)[0]:
        lead, resto = bruto.split(":", 1)
        if 0 < len(lead) <= 80:
            return f"<b>{escape(lead)}:</b> {escape(resto.strip())}"
    return escape(bruto)


def _linha_cadastro(rotulo, valor, style):
    texto = " ".join(str(valor or "").split())
    if not texto or texto == "—":
        return None
    return Paragraph(f"<b>{escape(rotulo)}:</b> {escape(texto)}", style)


def _endereco_proposta(lead) -> str:
    texto = _formatar_endereco_lead(lead).replace("nº ", "")
    return "" if texto == "—" else texto


def _texto_cadastro(valor) -> str:
    return valor.strip() if isinstance(valor, str) else ""


def _documento_exibicao(valor) -> str:
    """CPF e CNPJ saem com pontuação, mesmo quando o cadastro guarda só os dígitos."""
    texto = _texto_cadastro(valor)
    if not texto:
        return ""
    return normalizar_cpf_cnpj(texto) or texto


def _rotulo_documento(valor) -> str:
    import re
    digits = re.sub(r"\D", "", _texto_cadastro(valor))
    if len(digits) == 11:
        return "CPF"
    if len(digits) == 14:
        return "CNPJ"
    return "CPF/CNPJ"


def _valor_da_conta(lead, campo) -> str:
    conta = getattr(lead, "conta", None)
    if conta is None:
        return ""
    return _texto_cadastro(getattr(conta, campo, None))


def _nomes_da_empresa(lead):
    """Razão social e nome fantasia. O nome da conta é o nome fantasia."""
    razao = _valor_da_conta(lead, "razao_social") or _texto_cadastro(getattr(lead, "empresa", None))
    fantasia = _valor_da_conta(lead, "nome")
    return razao, fantasia


def _documento_do_cliente(lead) -> str:
    """Empresa vinculada mostra o CNPJ da conta. Pessoa física mostra o CPF do lead."""
    cnpj = _valor_da_conta(lead, "cnpj")
    if cnpj:
        return _documento_exibicao(cnpj)
    return _documento_exibicao(getattr(lead, "cpf_cnpj", None))


def _pessoa_do_contato(lead, *nomes_empresa) -> str:
    contato = getattr(lead, "contato", None)
    pessoa = _texto_cadastro(getattr(contato, "nome", None)) if contato is not None else ""
    if not pessoa:
        pessoa = _texto_cadastro(getattr(lead, "nome", None))
    empresas = {nome.casefold() for nome in nomes_empresa if nome}
    if pessoa.casefold() in empresas:
        return ""
    return pessoa


def _linhas_do_cliente(lead, style):
    """Empresa: razão social e nome fantasia, com a pessoa no contato. Pessoa física continua Cliente."""
    razao, fantasia = _nomes_da_empresa(lead)
    documento = _documento_do_cliente(lead)
    pessoa = _texto_cadastro(getattr(lead, "nome", None))
    empresa = _rotulo_documento(documento) == "CNPJ" or bool(razao or fantasia)
    if empresa and not razao and not fantasia:
        razao = pessoa
    linhas = []
    if empresa:
        if razao:
            linhas.append(_linha_cadastro("Razão social", razao, style))
        if fantasia:
            linhas.append(_linha_cadastro("Nome fantasia", fantasia, style))
        contato = _pessoa_do_contato(lead, razao, fantasia)
    else:
        linhas.append(_linha_cadastro("Cliente", pessoa, style))
        contato = ""
    linhas.append(_linha_cadastro(_rotulo_documento(documento), documento, style))
    linhas.append(_linha_cadastro("Endereço", _endereco_proposta(lead), style))
    telefone = _texto_cadastro(getattr(lead, "telefone", None))
    if telefone:
        telefone = telefone_exibicao_brasileiro(telefone) or telefone
    email = _texto_cadastro(getattr(lead, "email", None))
    if contato:
        partes = [contato]
        if telefone:
            partes.append(telefone)
        if email:
            partes.append(email)
        linhas.append(_linha_cadastro("Contato", " • ".join(partes), style))
    elif telefone and email:
        linhas.append(_linha_cadastro("Contato", f"{telefone} • {email}", style))
    elif telefone:
        linhas.append(_linha_cadastro("Contato", telefone, style))
    else:
        linhas.append(_linha_cadastro("E-mail", email, style))
    return linhas


def _build_identificacao_visual(elements, loja_data, lead):
    """Representante e cliente em linhas curtas, com os dados do cadastro."""
    style = _estilo_corpo_proposta()
    _titulo_numerado(elements, 1, "Identificação")
    loja_data = loja_data or {}
    linhas = []
    if loja_data.get("nome"):
        linhas.append(_linha_cadastro("Representante", loja_data.get("nome"), style))
    documento = _documento_exibicao(loja_data.get("cpf_cnpj"))
    linhas.append(_linha_cadastro(_rotulo_documento(documento), documento, style))
    linhas.append(_linha_cadastro("Endereço", loja_data.get("endereco"), style))
    responsavel = _texto_cadastro(loja_data.get("admin_nome"))
    telefone = _texto_cadastro(loja_data.get("telefone"))
    if telefone:
        telefone = telefone_exibicao_brasileiro(telefone) or telefone
    if responsavel and telefone:
        linhas.append(_linha_cadastro("Responsável", f"{responsavel} • {telefone}", style))
    else:
        linhas.append(_linha_cadastro("Responsável", responsavel, style))
        linhas.append(_linha_cadastro("Telefone", telefone, style))
    linhas.append(_linha_cadastro("E-mail", loja_data.get("admin_email"), style))
    for linha in linhas:
        if linha is not None:
            elements.append(linha)
    if lead is None:
        return
    elements.append(Spacer(1, 0.22 * cm))
    for linha in _linhas_do_cliente(lead, style):
        if linha is not None:
            elements.append(linha)



__all__ = ['_par_logos', '_build_faixa_logos', '_estilo_titulo_proposta', '_estilo_titulo_recursos', '_estilo_subtitulo_proposta', '_estilo_secao_proposta', '_estilo_corpo_proposta', '_titulo_numerado', '_markup_linha', '_linha_cadastro', '_endereco_proposta', '_texto_cadastro', '_documento_exibicao', '_rotulo_documento', '_valor_da_conta', '_nomes_da_empresa', '_documento_do_cliente', '_pessoa_do_contato', '_linhas_do_cliente', '_build_identificacao_visual']
