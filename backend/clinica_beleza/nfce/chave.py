"""Chave de acesso e QR Code da NFC-e. Sem chamada à SEFAZ."""
from __future__ import annotations

import hashlib
import unicodedata

from core.fiscal_format import digitos, dinheiro  # noqa: F401

NS_NFE = "http://www.portalfiscal.inf.br/nfe"
UF_SP = "35"
MODELO = "65"
FRASE_HOMOLOGACAO_EMITENTE = "NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL"
FRASE_HOMOLOGACAO_ITEM = "NOTA FISCAL EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL"

QR_SP = {
    True: "https://www.homologacao.nfce.fazenda.sp.gov.br/qrcode",
    False: "https://www.nfce.fazenda.sp.gov.br/qrcode",
}
CONSULTA_SP = {
    True: "https://www.homologacao.nfce.fazenda.sp.gov.br/consulta",
    False: "https://www.nfce.fazenda.sp.gov.br/consulta",
}

TPAG = {
    "CASH": "01",
    "CREDIT_CARD": "03",
    "DEBIT_CARD": "04",
    "PIX": "17",
    "TRANSFER": "18",
    "PRAZO": "05",
}


def sem_acento(valor: str) -> str:
    base = unicodedata.normalize("NFKD", str(valor or ""))
    return "".join(ch for ch in base if not unicodedata.combining(ch))


def texto_fiscal(valor: str, limite: int) -> str:
    limpo = " ".join(sem_acento(valor).split())
    return (limpo or "NAO INFORMADO")[:limite]


def digito_chave(base: str) -> str:
    """Módulo 11 da chave, pesos de 2 a 9 da direita para a esquerda."""
    if not base.isdigit():
        raise ValueError("A base da chave precisa ter só dígitos.")
    peso = 2
    soma = 0
    for caractere in reversed(base):
        soma += int(caractere) * peso
        peso = 2 if peso == 9 else peso + 1
    resto = soma % 11
    return "0" if resto < 2 else str(11 - resto)


def montar_chave(*, cnpj: str, ano_mes: str, serie: int, numero: int, codigo: str, emissao: str = "1") -> str:
    """44 posições: UF, AAMM, documento, modelo 65, série, número, emissão, código e DV."""
    documento = digitos(cnpj, 14)
    base = (
        f"{UF_SP}{digitos(ano_mes, 4)}{documento}{MODELO}"
        f"{int(serie):03d}{int(numero):09d}{digitos(emissao, 1)}{digitos(codigo, 8)}"
    )
    if len(base) != 43:
        raise ValueError("A chave da NFC-e ficou incompleta.")
    return base + digito_chave(base)


def codigo_numerico(semente: int, numero: int) -> str:
    """Oito dígitos diferentes do número da nota e diferentes de zero."""
    bruto = f"{(int(semente) * 7919 + int(numero) * 104729) % 100000000:08d}"
    if bruto == "00000000" or int(bruto) == int(numero):
        bruto = f"{(int(bruto) + 1) % 100000000:08d}"
        if bruto == "00000000":
            bruto = "00000001"
    return bruto


def id_csc_qr(valor: str) -> str:
    texto = digitos(valor).lstrip("0")
    return texto or "0"


def url_qrcode(*, chave: str, homologacao: bool, id_csc: str, csc: str) -> str:
    ambiente = "2" if homologacao else "1"
    identificador = id_csc_qr(id_csc)
    carga = f"{chave}|2|{ambiente}|{identificador}|{csc}"
    resumo = hashlib.sha1(carga.encode("utf-8")).hexdigest().upper()
    return f"{QR_SP[homologacao]}?p={chave}|2|{ambiente}|{identificador}|{resumo}"


def unidade_fiscal(unidade: str) -> str:
    chave = sem_acento(unidade).strip().lower()
    mapa = {
        "unidade": "UN",
        "un": "UN",
        "und": "UN",
        "ampola": "UN",
        "frasco": "UN",
        "ml": "ML",
        "mg": "MG",
        "g": "G",
        "grama": "G",
        "kg": "KG",
    }
    return mapa.get(chave, "UN")
