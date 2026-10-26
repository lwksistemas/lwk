"""Formatação e utilitários para PDF de proposta/contrato."""
import logging
import re
import unicodedata
from html.parser import HTMLParser

import pytz
import requests

logger = logging.getLogger(__name__)

def _formatar_timestamp_local(assinado_em):
    """Converte timestamp UTC para timezone local (Brasil)."""
    tz_brasil = pytz.timezone("America/Sao_Paulo")
    return assinado_em.astimezone(tz_brasil).strftime("%d/%m/%Y %H:%M:%S")


def linguagem_investimento(texto: str) -> str:
    """Na proposta, cobrança e pagamento aparecem como investimento."""
    if not isinstance(texto, str) or not texto:
        return texto or ""

    def trocar(match):
        palavra = match.group(0)
        plural = palavra[-1:].lower() == "s"
        if palavra.isupper():
            return "INVESTIMENTOS" if plural else "INVESTIMENTO"
        if palavra[:1].isupper():
            return "Investimentos" if plural else "Investimento"
        return "investimentos" if plural else "investimento"

    return re.sub(r"\b[Pp]agamentos?\b|\b[Cc]obran[cç]as?\b", trocar, texto)


def _formatar_valor(valor):
    """Formata valor monetário para exibição."""
    if valor is None:
        return "—"
    try:
        v = float(valor)
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "—"


def _title_case_endereco(texto: str) -> str:
    """Normaliza capitalização de endereço: se tudo maiúsculo, converte para Title Case."""
    if not texto or texto == "—":
        return texto
    # Se mais de 60% das letras são maiúsculas, converter para title case
    letras = [c for c in texto if c.isalpha()]
    if letras and sum(1 for c in letras if c.isupper()) / len(letras) > 0.6:
        # Preservar siglas de estado (SP, PR, RJ, etc.) e CEP
        import re
        def _title_part(part):
            part = part.strip()
            if re.match(r"^[A-Z]{2}$", part):  # UF
                return part
            if re.match(r"^CEP\s", part, re.IGNORECASE):  # CEP XXXXX
                return part
            if re.match(r"^nº\s", part, re.IGNORECASE):  # nº 123
                return part
            return part.title()
        return ", ".join(_title_part(p) for p in texto.split(","))
    return texto


def _formatar_endereco_lead(lead):
    """Monta string de endereço do lead."""
    if not lead:
        return "—"
    parts = [
        getattr(lead, "logradouro", "") or "",
        f"nº {lead.numero}" if getattr(lead, "numero", "") else "",
        getattr(lead, "complemento", "") or "",
        getattr(lead, "bairro", "") or "",
        (f"{lead.cidade}/{lead.uf}" if (getattr(lead, "cidade", "") and getattr(lead, "uf", ""))
         else (getattr(lead, "cidade", "") or getattr(lead, "uf", ""))),
        f"CEP {lead.cep}" if getattr(lead, "cep", "") else "",
    ]
    raw = ", ".join(p for p in parts if p).strip() or "—"
    return _title_case_endereco(raw)


def _formatar_nome_usuario(user):
    """Tenta montar um nome legível para o usuário (vendedor)."""
    if not user:
        return "—"
    first = getattr(user, "first_name", "") or ""
    last = getattr(user, "last_name", "") or ""
    full = f"{first} {last}".strip()
    return full or getattr(user, "nome", "") or getattr(user, "username", "") or "—"


def descricao_util_na_proposta(texto: str) -> bool:
    """Rótulo curto do plano, como "Ultrasis Laudos - Mensal", não entra na proposta."""
    limpo = " ".join((texto or "").split())
    if not limpo:
        return False
    if len(limpo) >= 60:
        return True
    return any(marca in limpo for marca in ".:;")


def _textos_dos_itens(oportunidade) -> list[str]:
    if oportunidade is None:
        return []
    relacao = getattr(oportunidade, "itens", None)
    if relacao is None:
        return []
    if hasattr(relacao, "select_related"):
        itens = relacao.select_related("produto_servico").all()
    else:
        itens = relacao
    textos = []
    for item in itens:
        produto = getattr(item, "produto_servico", None)
        texto = " ".join((getattr(produto, "descricao", None) or "").split())
        if texto and texto not in textos:
            textos.append(texto)
    return textos


def descricoes_da_oportunidade(oportunidade) -> list[str]:
    """Descrições dos serviços escolhidos na oportunidade, sem repetir."""
    return [texto for texto in _textos_dos_itens(oportunidade) if descricao_util_na_proposta(texto)]


def _rotulos_da_oportunidade(oportunidade) -> set[str]:
    return {texto for texto in _textos_dos_itens(oportunidade) if not descricao_util_na_proposta(texto)}


def linhas_resumo_investimento(
    *,
    unico=0,
    mensal=0,
    trimestral=0,
    semestral=0,
    anual=0,
    valor_total=None,
    desconto_valor=0,
    desconto_tipo="percentual",
    valor_com_desconto=None,
) -> tuple[list[tuple[str, str]], str]:
    """Pagamento inicial e as cobranças seguintes, lidos dos itens da oportunidade."""
    unico = float(unico or 0)
    mensal = float(mensal or 0)
    trimestral = float(trimestral or 0)
    semestral = float(semestral or 0)
    anual = float(anual or 0)
    inicial = unico + mensal + trimestral + semestral + anual
    if valor_total is None:
        valor_total = inicial
    linhas = [("Investimento inicial:", _formatar_valor(valor_total))]
    partes = []
    if unico > 0:
        partes.append(f"{_formatar_valor(unico)} de implantação")
    if mensal > 0:
        partes.append(f"{_formatar_valor(mensal)} da primeira mensalidade")
    if trimestral > 0:
        partes.append(f"{_formatar_valor(trimestral)} do primeiro trimestre")
    if semestral > 0:
        partes.append(f"{_formatar_valor(semestral)} do primeiro semestre")
    if anual > 0:
        partes.append(f"{_formatar_valor(anual)} do primeiro ano")
    frases = []
    if len(partes) >= 2:
        frases.append("Inclui " + " + ".join(partes) + ".")
    if unico > 0:
        frases.append("As taxas de implantação são cobradas uma única vez.")
    if mensal > 0:
        linhas.append(("Mensalidades seguintes:", f"{_formatar_valor(mensal)}/mês"))
    if trimestral > 0:
        linhas.append(("Trimestres seguintes:", f"{_formatar_valor(trimestral)}/trimestre"))
    if semestral > 0:
        linhas.append(("Semestres seguintes:", f"{_formatar_valor(semestral)}/semestre"))
    if anual > 0:
        linhas.append(("Anos seguintes:", f"{_formatar_valor(anual)}/ano"))
    desconto = float(desconto_valor or 0)
    if desconto > 0:
        if desconto_tipo == "percentual":
            linhas.append(("Desconto:", f"{desconto_valor}%"))
        else:
            linhas.append(("Desconto:", _formatar_valor(desconto_valor)))
        final = valor_com_desconto if valor_com_desconto is not None else valor_total
        linhas.append(("Valor com desconto:", _formatar_valor(final)))
    return linhas, " ".join(frases)


def texto_resumo_visual(linhas, frase) -> list[tuple[str, bool]]:
    """Ordem da proposta: pagamento inicial, o que ele inclui, cobranças seguintes e a taxa única."""
    inclui = ""
    taxas = ""
    for parte in re.split(r"(?<=\.)\s+", frase or ""):
        texto = parte.strip()
        if not texto:
            continue
        if texto.lower().startswith("inclui"):
            inclui = texto
        else:
            taxas = texto
    blocos = []
    seguintes = []
    extras = []
    for indice, (rotulo, valor) in enumerate(linhas):
        texto = f"{rotulo} {valor}".strip()
        if indice == 0:
            blocos.append((texto, True))
        elif rotulo.startswith("Desconto") or rotulo.startswith("Valor com"):
            extras.append((texto, True))
        else:
            if not texto.endswith("."):
                texto += "."
            seguintes.append((texto, True))
    if inclui:
        blocos.append((inclui, False))
    blocos.extend(seguintes)
    if taxas:
        blocos.append((taxas, False))
    blocos.extend(extras)
    return blocos


def titulo_de_bloco(bloco) -> str:
    """Linha curta do template vira título de seção. O resto continua parágrafo."""
    if not isinstance(bloco, str):
        return ""
    bruto = bloco.strip()
    if bruto.startswith("# "):
        return bruto[2:].strip()
    if not bruto or len(bruto) > 60 or len(bruto.split()) > 8:
        return ""
    if any(marca in bruto for marca in ".:;•"):
        return ""
    return bruto


MARCA_SEGUNDA_FOLHA = "[[folha:2]]"

LETRAS_PDF = {
    "padrao": ("DejaVu", "DejaVu-Bold"),
    "times": ("Times-Roman", "Times-Bold"),
    "helvetica": ("Helvetica", "Helvetica-Bold"),
    "courier": ("Courier", "Courier-Bold"),
}
TAMANHOS_LETRA = {8, 9, 10, 11, 12, 14}


def conteudo_tem_formatacao(conteudo: str) -> bool:
    bruto = (conteudo or "").lower()
    return "<span" in bruto or "data-align" in bruto or "data-bold" in bruto or "text-align" in bruto


def dividir_texto_folhas(conteudo: str):
    """Divide o texto bruto na marca da segunda folha, sem interpretar HTML."""
    if MARCA_SEGUNDA_FOLHA not in (conteudo or ""):
        return None
    esquerda, direita = conteudo.split(MARCA_SEGUNDA_FOLHA, 1)
    return esquerda.strip(), direita.strip()


class _LeitorBlocos(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocos = []
        self.atual = None
        self.pilha = []

    def _abrir(self, align):
        self._fechar()
        self.atual = {"align": align or "left", "trechos": []}

    def _fechar(self):
        if self.atual is None:
            return
        texto = "".join(trecho["texto"] for trecho in self.atual["trechos"]).replace("\xa0", " ")
        if not texto.strip():
            texto = ""
            self.atual["trechos"] = [{"texto": "", "fonte": None, "tamanho": None, "negrito": False}]
        self.atual["texto"] = texto
        self.blocos.append(self.atual)
        self.atual = None

    def _adicionar(self, data):
        fonte, tamanho, negrito = self.pilha[-1] if self.pilha else (None, None, False)
        self.atual["trechos"].append({"texto": data, "fonte": fonte, "tamanho": tamanho, "negrito": negrito})

    def handle_starttag(self, tag, attrs):
        atributos = {chave: valor for chave, valor in attrs}
        if tag in ("p", "div"):
            estilo = atributos.get("style") or ""
            align = atributos.get("data-align") or ""
            if not align:
                marca = re.search(r"text-align\s*:\s*(left|center|right|justify)", estilo, re.I)
                align = marca.group(1).lower() if marca else "left"
            if align not in ("left", "center", "right", "justify"):
                align = "left"
            self._abrir(align)
        elif tag == "span":
            anterior = self.pilha[-1] if self.pilha else (None, None, False)
            tamanho = atributos.get("data-size")
            if str(tamanho or "").isdigit():
                tamanho = int(tamanho)
            else:
                tamanho = anterior[1]
            if "data-bold" in atributos:
                negrito = atributos.get("data-bold") not in ("0", "false")
            else:
                negrito = anterior[2]
            self.pilha.append((atributos.get("data-font") or anterior[0], tamanho, negrito))
        elif tag == "br" and self.atual is not None:
            self._adicionar("\n")

    def handle_endtag(self, tag):
        if tag in ("p", "div"):
            self._fechar()
        elif tag == "span" and self.pilha:
            self.pilha.pop()

    def handle_data(self, data):
        if self.atual is None:
            if not data.strip():
                return
            self._abrir("left")
        self._adicionar(data)


def blocos_formatados(texto: str) -> list[dict]:
    """Parágrafos com alinhamento e trechos de letra. Texto puro vira uma linha por bloco."""
    bruto = (texto or "").strip()
    if not bruto:
        return []
    if re.search(r"<(p|div|span)\b", bruto, re.I):
        leitor = _LeitorBlocos()
        leitor.feed(bruto)
        leitor.close()
        leitor._fechar()
        return leitor.blocos
    return [
        {"align": "left", "trechos": [{"texto": linha, "fonte": None, "tamanho": None}], "texto": linha}
        for linha in bruto.replace("\r\n", "\n").split("\n")
    ]


def extrair_letra_do_template(conteudo: str) -> tuple[str, str, str, int]:
    """Tira a marca de tipo e tamanho. Sem marca, o PDF segue na letra padrão, corpo 9."""
    texto = (conteudo or "").replace("\r\n", "\n")
    tipo = "padrao"
    tamanho = 9
    saida = []
    for linha in texto.split("\n"):
        marca = re.fullmatch(r"\[\[letra:([a-z]+)\|(\d+)\]\]", linha.strip())
        if marca:
            tipo = marca.group(1)
            tamanho = int(marca.group(2))
            continue
        saida.append(linha)
    fonte, negrito = LETRAS_PDF.get(tipo, LETRAS_PDF["padrao"])
    if tamanho not in TAMANHOS_LETRA:
        tamanho = 9
    return "\n".join(saida).strip(), fonte, negrito, tamanho


def texto_legivel(conteudo: str) -> str:
    """O mesmo texto do template, sem as marcas HTML do editor."""
    texto = (conteudo or "").replace("\r\n", "\n")
    if not re.search(r"</?[a-z][^>]*>", texto, re.I):
        return re.sub(r"\n{3,}", "\n\n", texto).strip()
    texto = re.sub(r"<p>\s*<br\s*/?>\s*</p>", "\n", texto, flags=re.I)
    texto = re.sub(r"<br\s*/?>", "\n", texto, flags=re.I)
    texto = re.sub(r"</p>", "\n", texto, flags=re.I)
    texto = re.sub(r"</div>", "\n", texto, flags=re.I)
    texto = re.sub(r"<[^>]+>", "", texto)
    for origem, destino in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">")):
        texto = texto.replace(origem, destino)
    texto = re.sub(r"[ \t]+\n", "\n", texto)
    return re.sub(r"\n{3,}", "\n\n", texto).strip()


def conteudo_formatado_do_template(conteudo_proposta: str, conteudos_template) -> str:
    """Se o texto da proposta é o de um template, o PDF usa o negrito e os espaços dele."""
    proposta = (conteudo_proposta or "").strip()
    assinatura = " ".join(texto_legivel(proposta).split())
    if not assinatura:
        return proposta
    for original in conteudos_template or []:
        bruto = (original or "").strip()
        if bruto and " ".join(texto_legivel(bruto).split()) == assinatura:
            return bruto
    return proposta


def escolher_conteudo_narrativo(conteudo_proposta: str, conteudo_template: str) -> str:
    """A proposta que já gravou um template com as duas folhas usa esse texto.

    Uma cópia antiga, de antes da separação, ainda acompanha o template padrão
    da prestadora. Assim a primeira folha escrita no padrão continua no PDF.
    """
    proposta = (conteudo_proposta or "").strip()
    template = (conteudo_template or "").strip()
    if MARCA_SEGUNDA_FOLHA in proposta:
        return proposta
    if MARCA_SEGUNDA_FOLHA in template:
        return template
    return proposta


def conteudo_narrativo_da_proposta(proposta) -> str:
    from crm_vendas.models import PropostaTemplate

    oportunidade = getattr(proposta, "oportunidade", None)
    prestadora_id = getattr(oportunidade, "empresa_prestadora_id", None) if oportunidade is not None else None
    proposta_txt = getattr(proposta, "conteudo", "") or ""
    conteudos = []
    template = ""
    if isinstance(prestadora_id, int):
        registros = list(
            PropostaTemplate.objects.filter(prestadora_id=prestadora_id, ativo=True).order_by("-updated_at")
        )
        conteudos = [getattr(registro, "conteudo", "") or "" for registro in registros]
        padrao = next((registro for registro in registros if registro.is_padrao), None)
        template = getattr(padrao, "conteudo", "") or ""
    formatado = conteudo_formatado_do_template(proposta_txt, conteudos)
    if formatado != proposta_txt.strip():
        return formatado
    return escolher_conteudo_narrativo(proposta_txt, template)


def dividir_folhas_marcadas(paragrafos):
    """O editor grava a primeira folha e as seguintes separadas por esta marca."""
    blocos = list(paragrafos or [])
    if MARCA_SEGUNDA_FOLHA not in blocos:
        return None
    indice = blocos.index(MARCA_SEGUNDA_FOLHA)
    primeira = blocos[:indice]
    seguintes = blocos[indice + 1 :]
    while primeira and primeira[-1] == "":
        primeira.pop()
    while seguintes and seguintes[0] == "":
        seguintes.pop(0)
    return primeira, seguintes


def titulo_e_corpo_da_primeira_folha(paragrafos) -> tuple[str, list[str]]:
    """A primeira linha curta vira o título. O restante sai logo abaixo, com as linhas em branco."""
    blocos = list(paragrafos or [])
    while blocos and blocos[0] == "":
        blocos.pop(0)
    if not blocos:
        return "", []
    titulo = titulo_de_bloco(blocos[0])
    if titulo:
        return titulo, blocos[1:]
    return "", blocos


def partir_condicoes(paragrafos) -> tuple[list[str], list[dict]]:
    """Separa o texto livre das seções. Um título é linha curta ou começa com '# '.

    O bloco de pagamento fica inteiro na primeira folha até a linha em branco,
    mesmo quando uma linha curta pareceria outro título.
    """
    intro = []
    secoes = []
    atual = None
    segurando_pagamento = False
    for bloco in paragrafos or []:
        if bloco == "":
            if segurando_pagamento:
                segurando_pagamento = False
                atual = None
                continue
            destino = intro if atual is None else atual["paragrafos"]
            destino.append(bloco)
            continue
        if segurando_pagamento and atual is not None:
            atual["paragrafos"].append(bloco)
            continue
        titulo = titulo_de_bloco(bloco)
        if titulo:
            atual = {"titulo": titulo, "paragrafos": []}
            secoes.append(atual)
            segurando_pagamento = eh_dados_pagamento(titulo)
            continue
        if atual is None:
            intro.append(bloco)
        else:
            atual["paragrafos"].append(bloco)
    return intro, secoes


_ORDEM_VERSAO = (
    "Sistema de Laudos",
    "Sistema de Clínica",
    "Captura DICOM",
    "Worklist",
    "Ultracap",
)


def _sem_acento(texto: str) -> str:
    base = unicodedata.normalize("NFD", (texto or "").casefold())
    return "".join(letra for letra in base if unicodedata.category(letra) != "Mn")


def rotulo_versao_contratada(nome: str) -> str:
    """Nome curto da versão. O plano e a quantidade ficam na tabela."""
    chave = _sem_acento(nome)
    if "worklist" in chave:
        return "Worklist"
    if "dicom" in chave:
        return "Captura DICOM"
    if "laudo" in chave:
        return "Sistema de Laudos"
    if "clinica" in chave:
        return "Sistema de Clínica"
    if "ultracap" in chave:
        return "Ultracap"
    texto = " ".join((nome or "").split())
    return re.sub(r"\s*[•·]\s*\d+\s+aparelhos?$", "", texto, flags=re.IGNORECASE).strip()


def subtitulo_da_versao(itens) -> str:
    """O subtítulo lista só as versões recorrentes que estão na proposta."""
    rotulos = []
    for item in itens or []:
        produto = getattr(item, "produto_servico", None) or item
        recorrencia = getattr(produto, "recorrencia", None) or "unico"
        if recorrencia == "unico":
            continue
        rotulo = rotulo_versao_contratada(getattr(produto, "nome", "") or "")
        if rotulo and rotulo not in rotulos:
            rotulos.append(rotulo)
    conhecidos = [nome for nome in _ORDEM_VERSAO if nome in rotulos]
    demais = [nome for nome in rotulos if nome not in _ORDEM_VERSAO]
    return " • ".join(conhecidos + demais)


def separar_subtitulo(paragrafos) -> tuple[str, list]:
    """A primeira linha curta, sem pontuação de frase, é o subtítulo da proposta."""
    blocos = list(paragrafos or [])
    if not blocos:
        return "", blocos
    primeiro = (blocos[0] or "").strip()
    if (
        primeiro
        and len(primeiro) <= 90
        and not any(marca in primeiro for marca in ".:;")
        and not titulo_de_bloco(primeiro)
    ):
        return primeiro, blocos[1:]
    return "", blocos


def eh_dados_pagamento(titulo: str) -> bool:
    texto = " ".join((titulo or "").replace("#", "").split()).lower()
    return "dados" in texto and "pagamento" in texto


def extrair_pagamento_inicial(intro, secoes) -> tuple[str, list[str], list, list]:
    """Os dados bancários saem do template e vão para a primeira folha."""
    pagamento = []
    titulo = ""
    novas = []
    for secao in secoes:
        if eh_dados_pagamento(secao["titulo"]) and not titulo:
            titulo = secao["titulo"].strip()
            pagamento = [p for p in secao["paragrafos"] if p]
        else:
            novas.append(secao)
    if titulo:
        return titulo, pagamento, list(intro), novas
    novo_intro = []
    capturando = False
    for bloco in intro:
        if not capturando and eh_dados_pagamento(bloco):
            capturando = True
            titulo = bloco.strip()
            continue
        if capturando:
            if bloco == "":
                if pagamento:
                    capturando = False
                continue
            if titulo_de_bloco(bloco):
                capturando = False
                novo_intro.append(bloco)
                continue
            pagamento.append(bloco)
            continue
        novo_intro.append(bloco)
    return titulo, pagamento, novo_intro, novas


def paragrafos_condicoes(conteudo, oportunidade) -> list[str]:
    """Texto do template, sem a descrição dos serviços. Essa descrição tem seção própria."""
    bruto = (conteudo or "").strip()
    if not bruto:
        return []
    descricoes = descricoes_da_oportunidade(oportunidade)
    rotulos = _rotulos_da_oportunidade(oportunidade)
    blocos = _html_to_paragraphs(bruto)
    if blocos == ["Conteúdo não informado."]:
        return []
    saida = []
    for bloco in blocos:
        if bloco == "":
            if saida and saida[-1] != "":
                saida.append("")
            continue
        normal = " ".join(bloco.split())
        if normal in rotulos or normal in descricoes:
            continue
        resto = normal
        for descricao in descricoes:
            resto = resto.replace(descricao, " ")
        resto = " ".join(resto.split())
        if not resto:
            continue
        saida.append(resto if resto != normal else bloco)
    while saida and saida[-1] == "":
        saida.pop()
    return saida


def conteudo_com_descricoes(conteudo, oportunidade) -> str:
    """Inclui no conteúdo a descrição de cada serviço da oportunidade."""
    base = (conteudo or "").strip()
    rotulos = _rotulos_da_oportunidade(oportunidade)
    if rotulos and base:
        paragrafos = re.split(r"\n{2,}", base)
        base = "\n\n".join(
            paragrafo for paragrafo in paragrafos if " ".join(paragrafo.split()) not in rotulos
        ).strip()
    faltam = [texto for texto in descricoes_da_oportunidade(oportunidade) if texto not in base]
    if not faltam:
        return base
    bloco = "\n\n".join(faltam)
    if not base:
        return bloco
    return f"{base}\n\n{bloco}"


def _html_to_paragraphs(html):
    """Converte HTML/texto do conteúdo em lista de parágrafos para o PDF."""
    if not html:
        return ["Conteúdo não informado."]
    text = str(html)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</(?:p|div|li|h[1-6])>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<li[^>]*>", "• ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
    lines = text.split("\n")
    paragraphs = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            paragraphs.append(stripped)
        elif paragraphs:
            paragraphs.append("")
    return paragraphs or ["Conteúdo não informado."]


def _montar_endereco_loja(loja) -> str | None:
    """Monta endereço formatado da loja."""
    cidade = getattr(loja, "cidade", "") or ""
    uf = getattr(loja, "uf", "") or ""
    cidade_uf = f"{cidade}/{uf}" if (cidade and uf) else (cidade or uf)
    parts = [
        getattr(loja, "logradouro", "") or "",
        getattr(loja, "numero", "") or "",
        getattr(loja, "complemento", "") or "",
        getattr(loja, "bairro", "") or "",
        cidade_uf,
        f"CEP {loja.cep}" if getattr(loja, "cep", "") else "",
    ]
    return ", ".join(p for p in parts if p).strip() or None


def _montar_admin_loja(owner) -> tuple[str | None, str | None]:
    """Retorna (admin_nome, admin_email) a partir do owner da loja."""
    if not owner:
        return None, None
    admin_nome = f"{getattr(owner, 'first_name', '') or ''} {getattr(owner, 'last_name', '') or ''}".strip() or getattr(owner, "username", "") or None
    admin_email = getattr(owner, "email", None) or None
    return admin_nome, admin_email


def baixar_logo_pdf(logo_url: str) -> bytes | None:
    """Baixa a logomarca. A mídia só entrega o arquivo com a assinatura do endereço."""
    bruto = (logo_url or "").strip()
    if not bruto:
        return None
    try:
        from core.media_storage import assinar_url_midia

        resposta = requests.get(assinar_url_midia(bruto), timeout=8, allow_redirects=False)
    except Exception:
        logger.warning("Erro ao baixar a logomarca da proposta")
        return None
    if resposta.status_code != 200 or not resposta.content:
        return None
    return resposta.content


def _obter_dados_loja(loja_id):
    """Obtém dados da loja do superadmin (nome, endereço, CPF/CNPJ, admin, logo, telefone)."""
    try:
        from superadmin.models import Loja
        loja = Loja.objects.using("default").filter(id=loja_id).select_related("owner").first()
        if not loja:
            return {}
        from superadmin.loja_utils import contato_publico_loja

        endereco = _montar_endereco_loja(loja)
        admin_nome, admin_email = _montar_admin_loja(getattr(loja, "owner", None))
        telefone, email_publico = contato_publico_loja(loja)
        return {
            "nome": getattr(loja, "nome", "") or "",
            "endereco": endereco,
            "cpf_cnpj": getattr(loja, "cpf_cnpj", "") or None,
            "telefone": telefone or None,
            "email": email_publico or None,
            "admin_nome": admin_nome,
            "admin_email": admin_email,
            "logo": (getattr(loja, "logo", "") or "").strip() or None,
            "login_logo": (getattr(loja, "login_logo", "") or "").strip() or None,
        }
    except Exception:
        return {}
