from ._pdf_base import *  # noqa: F401,F403
from .secoes_logo import *  # noqa: F401,F403
from .secoes_classicas import *  # noqa: F401,F403
from .secoes_identificacao import *  # noqa: F401,F403
from .secoes_investimento import *  # noqa: F401,F403

def _sem_acento(texto: str) -> str:
    import unicodedata
    base = unicodedata.normalize("NFD", (texto or "").lower())
    return "".join(letra for letra in base if unicodedata.category(letra) != "Mn")


def _estilo_paragrafo_proposta(fonte=None, tamanho=9):
    nome = fonte or FONTE
    return ParagraphStyle(
        f"ParagrafoProposta{nome}{tamanho}",
        fontName=nome,
        fontSize=tamanho,
        textColor=COR_TEXTO,
        leading=tamanho + 4,
        spaceBefore=1,
        spaceAfter=6,
    )


def _build_recursos_visuais(elements, oportunidade, intro, secoes, fonte=None, fonte_negrito=None, tamanho=9):
    """Segunda folha: o que está incluído e as seções escritas no template."""
    corpo = _estilo_paragrafo_proposta(fonte, tamanho)
    estilo_titulo = _estilo_secao_proposta(fonte_negrito, min(tamanho + 2, 16))
    numero = 3
    incluidos = _descricoes_incluidas(oportunidade)
    if incluidos:
        _titulo_numerado(elements, numero, "O que está incluído", estilo_titulo)
        numero += 1
        for nome, texto in incluidos:
            if ":" in texto:
                elements.append(Paragraph(_markup_linha(texto), corpo))
            else:
                elements.append(Paragraph(f"<b>{escape(nome)}:</b> {escape(texto)}", corpo))
    for texto in intro:
        if texto == "":
            elements.append(Spacer(1, 0.12 * cm))
            continue
        elements.append(Paragraph(_markup_linha(texto), corpo))
    implantacao = _linhas_implantacao(oportunidade)
    if implantacao and not any("implant" in _sem_acento(secao["titulo"]) for secao in secoes):
        secoes = list(secoes) + [{"titulo": "Implantação e liberação", "paragrafos": implantacao}]
    for secao in secoes:
        _titulo_numerado(elements, numero, secao["titulo"], estilo_titulo)
        numero += 1
        paragrafos = list(secao["paragrafos"])
        for paragrafo in paragrafos:
            if paragrafo == "":
                elements.append(Spacer(1, 0.12 * cm))
                continue
            elements.append(Paragraph(_markup_linha(paragrafo), corpo))


_FACES_SELECAO = {
    "padrao": ("DejaVu", "DejaVu-Bold"),
    "times": ("Times-Roman", "Times-Bold"),
    "helvetica": ("Helvetica", "Helvetica-Bold"),
    "courier": ("Courier", "Courier-Bold"),
}
_ALINHAR = {"left": TA_LEFT, "center": TA_CENTER, "right": TA_RIGHT, "justify": TA_JUSTIFY}
_estilo_formatado_seq = 0


def _face_selecionada(tipo, negrito, fonte_padrao, fonte_negrito):
    if tipo in _FACES_SELECAO:
        normal, bold = _FACES_SELECAO[tipo]
        return bold if negrito else normal
    return fonte_negrito if negrito else fonte_padrao


def _estilo_formatado(fonte, tamanho, alinhamento, cor, espaco_depois):
    global _estilo_formatado_seq
    _estilo_formatado_seq += 1
    return ParagraphStyle(
        f"TplFmt{_estilo_formatado_seq}",
        fontName=fonte,
        fontSize=tamanho,
        textColor=cor,
        leading=tamanho + 4,
        alignment=_ALINHAR.get(alinhamento, TA_LEFT),
        spaceBefore=1,
        spaceAfter=espaco_depois,
    )


def _markup_trechos(bloco, fonte_padrao, fonte_negrito, tamanho_padrao, negrito=False):
    partes = []
    for trecho in bloco["trechos"]:
        texto = linguagem_investimento(trecho.get("texto") or "")
        if texto == "":
            continue
        face = _face_selecionada(trecho.get("fonte"), negrito or bool(trecho.get("negrito")), fonte_padrao, fonte_negrito)
        size = trecho.get("tamanho") or tamanho_padrao
        miolo = escape(texto).replace("\n", "<br/>")
        partes.append(f'<font face="{face}" size="{size}">{miolo}</font>')
    return "".join(partes)


def _flowable_bloco(bloco, fonte, fonte_negrito, tamanho, negrito=False, espaco_depois=2):
    texto = (bloco.get("texto") or "").strip()
    if not texto:
        return Spacer(1, 0.35 * cm)
    tem_fonte = any(
        trecho.get("fonte") or trecho.get("tamanho") or trecho.get("negrito")
        for trecho in bloco["trechos"] if trecho.get("texto")
    )
    tamanho_bloco = next((trecho.get("tamanho") for trecho in bloco["trechos"] if trecho.get("tamanho")), None)
    if negrito:
        tamanho_efetivo = tamanho_bloco or min(tamanho + 2, 16)
        fonte_efetiva = _face_selecionada(bloco["trechos"][0].get("fonte") if bloco["trechos"] else None, True, fonte, fonte_negrito)
        cor = COR_PROPOSTA
    else:
        tamanho_efetivo = tamanho_bloco or tamanho
        fonte_efetiva = fonte
        cor = COR_TEXTO
    estilo = _estilo_formatado(fonte_efetiva, tamanho_efetivo, bloco.get("align") or "left", cor, espaco_depois)
    if tem_fonte or negrito:
        markup = _markup_trechos(bloco, fonte, fonte_negrito, tamanho_efetivo, negrito)
    else:
        markup = _markup_linha(texto) or escape(texto)
    if not markup:
        return Spacer(1, 0.12 * cm)
    return Paragraph(markup, estilo)


def _sem_descricao_de_produto(blocos, oportunidade):
    descricoes = {" ".join(texto.split()) for texto in descricoes_da_oportunidade(oportunidade)}
    if not descricoes:
        return blocos
    return [bloco for bloco in blocos if " ".join((bloco.get("texto") or "").split()) not in descricoes]


def _titulo_formatado(bloco):
    texto = " ".join((bloco.get("texto") or "").split())
    return bool(texto) and "\n" not in (bloco.get("texto") or "") and bool(titulo_de_bloco(texto))


def desenhar_primeira_folha_formatada(elements, blocos, fonte, fonte_negrito, tamanho):
    """Primeira folha escrita no template, com a letra e o alinhamento de cada trecho."""
    blocos = [bloco for bloco in blocos if bloco.get("texto") is not None]
    while blocos and not (blocos[0].get("texto") or "").strip():
        blocos.pop(0)
    if not blocos:
        return
    elements.append(Spacer(1, 0.22 * cm))
    inicio = 0
    if _titulo_formatado(blocos[0]):
        elements.append(_flowable_bloco(blocos[0], fonte, fonte_negrito, tamanho, negrito=True, espaco_depois=4))
        inicio = 1
    for bloco in blocos[inicio:]:
        elements.append(_flowable_bloco(bloco, fonte, fonte_negrito, tamanho, espaco_depois=1))


def desenhar_recursos_formatados(elements, oportunidade, blocos, fonte, fonte_negrito, tamanho):
    """Segunda folha: incluídos da oportunidade e o texto do template já formatado."""
    blocos = _sem_descricao_de_produto(list(blocos or []), oportunidade)
    corpo = _estilo_paragrafo_proposta(fonte, tamanho)
    estilo_titulo = _estilo_secao_proposta(fonte_negrito, min(tamanho + 2, 16))
    numero = 3
    incluidos = _descricoes_incluidas(oportunidade)
    if incluidos:
        _titulo_numerado(elements, numero, "O que está incluído", estilo_titulo)
        numero += 1
        for nome, texto in incluidos:
            if ":" in texto:
                elements.append(Paragraph(_markup_linha(texto), corpo))
            else:
                elements.append(Paragraph(f"<b>{escape(nome)}:</b> {escape(texto)}", corpo))
    implantacao = _linhas_implantacao(oportunidade)
    if implantacao and not any("implant" in _sem_acento(bloco.get("texto") or "") for bloco in blocos):
        blocos.append({"align": "left", "trechos": [{"texto": "Implantação e liberação", "fonte": None, "tamanho": None}], "texto": "Implantação e liberação"})
        for linha in implantacao:
            blocos.append({"align": "left", "trechos": [{"texto": linha, "fonte": None, "tamanho": None}], "texto": linha})
    for bloco in blocos:
        if not (bloco.get("texto") or "").strip():
            elements.append(Spacer(1, 0.12 * cm))
            continue
        if _titulo_formatado(bloco):
            prefixo = f"{numero:02d}  "
            numero += 1
            titulo = {
                "align": bloco.get("align") or "left",
                "trechos": [{"texto": prefixo + (bloco["trechos"][0].get("texto") or "").lstrip(), "fonte": bloco["trechos"][0].get("fonte"), "tamanho": bloco["trechos"][0].get("tamanho")}] + bloco["trechos"][1:],
                "texto": prefixo + (bloco.get("texto") or "").lstrip(),
            }
            elements.append(_flowable_bloco(titulo, fonte, fonte_negrito, tamanho, negrito=True, espaco_depois=4))
            continue
        if "implant" in _sem_acento(bloco.get("texto") or "") and bloco.get("texto", "").strip() == "Implantação e liberação":
            elements.append(_flowable_bloco(bloco, fonte, fonte_negrito, tamanho, negrito=True, espaco_depois=4))
            continue
        elements.append(_flowable_bloco(bloco, fonte, fonte_negrito, tamanho, espaco_depois=4))




__all__ = ['_sem_acento', '_estilo_paragrafo_proposta', '_build_recursos_visuais', '_face_selecionada', '_estilo_formatado', '_markup_trechos', '_flowable_bloco', '_sem_descricao_de_produto', '_titulo_formatado', 'desenhar_primeira_folha_formatada', 'desenhar_recursos_formatados']
