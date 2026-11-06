"""Nomes e endereços no comprovante, sem o caixa-alta do cadastro."""
import re
_UNIDADE_RECIBO = {
    "ml": "mL",
    "mg": "mg",
    "g": "g",
    "un": "un",
    "ui": "UI",
    "mcg": "mcg",
    "ug": "µg",
    "µg": "µg",
}
_QTD_NO_NOME = re.compile(
    r"^(?P<nome>.*?)\s+(?P<qtd>\d+(?:[.,]\d+)?)\s*(?P<un>ml|mg|mcg|µg|ug|ui|un|g)$",
    re.IGNORECASE,
)


_MIUDAS_RECIBO = {
    "de", "da", "do", "das", "dos", "e", "em", "com", "para", "por", "a", "o", "as", "os",
}
_SIGLAS_RECIBO = {"fps", "spf", "uv", "uva", "uvb", "led", "dna", "aha", "bha"}
_UNIDADE_COLADA = re.compile(r"^(\d+(?:[.,]\d+)?)(ml|mg|mcg|µg|ug|ui|un|g)$", re.IGNORECASE)


def nome_exibicao_procedimento_recibo(nome: str) -> str:
    """Junta a dose ao procedimento e tira o caixa-alta do cadastro.

    ``PREENCHIMENTO DE GLÚTEOS 100 ML`` vira ``Preenchimento de Glúteos — 100 mL``.
    ``LIMPEZA DE PELE PROFUNDA`` vira ``Limpeza de Pele Profunda``.
    Nome que já veio com maiúsculas e minúsculas permanece.
    """
    texto = " ".join(str(nome or "").split())
    if not texto:
        return ""
    qtd = ""
    achado = _QTD_NO_NOME.match(texto)
    if achado:
        texto = achado.group("nome").strip(" -–—")
        unidade = _UNIDADE_RECIBO.get(achado.group("un").casefold(), achado.group("un"))
        qtd = f"{achado.group('qtd')} {unidade}"
    if _nome_em_caixa_alta(texto):
        texto = _frase_recibo(texto)
    if qtd:
        return f"{texto} — {qtd}"
    return texto


def _nome_em_caixa_alta(texto: str) -> bool:
    letras = [c for c in texto if c.isalpha()]
    return bool(letras) and all(c.isupper() for c in letras)


def _frase_recibo(texto: str) -> str:
    """Primeira letra de cada palavra. 'de' e 'da' ficam minúsculas, como na prévia."""
    palavras = []
    for indice, palavra in enumerate(texto.split()):
        unidade = _UNIDADE_COLADA.fullmatch(palavra)
        if unidade:
            sigla = _UNIDADE_RECIBO.get(unidade.group(2).casefold(), unidade.group(2))
            palavras.append(f"{unidade.group(1)} {sigla}")
            continue
        baixa = palavra.casefold()
        if baixa == "ph":
            palavras.append("pH")
            continue
        if baixa in _SIGLAS_RECIBO:
            palavras.append(baixa.upper())
            continue
        if indice and baixa in _MIUDAS_RECIBO:
            palavras.append(baixa)
            continue
        palavras.append(baixa[:1].upper() + baixa[1:])
    return " ".join(palavras)


_UF_RECIBO = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG",
    "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}


def texto_cadastro_recibo(texto: str) -> str:
    """Tira o caixa-alta do endereço gravado. Sigla de estado permanece."""
    texto = " ".join(str(texto or "").split())
    if not texto or not _nome_em_caixa_alta(texto):
        return texto
    palavras = []
    for indice, palavra in enumerate(texto.split()):
        nucleo = palavra.strip(",.;")
        sufixo = palavra[len(nucleo):]
        if nucleo.upper() in _UF_RECIBO and nucleo.isalpha():
            palavras.append(nucleo.upper() + sufixo)
            continue
        baixa = palavra.casefold()
        miuda = baixa.strip(",.;")
        if indice and miuda in _MIUDAS_RECIBO:
            palavras.append(baixa)
            continue
        if not baixa[:1].isalpha():
            palavras.append(palavra)
            continue
        palavras.append(baixa[:1].upper() + baixa[1:])
    return " ".join(palavras)
