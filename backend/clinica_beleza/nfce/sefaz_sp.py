"""Envio da NFC-e para a SEFAZ-SP."""
from __future__ import annotations

import defusedxml.ElementTree as ET

from ..estoque_nfe_sefaz import SefazNfeErro, envelope_soap, pem_do_pfx, postar_soap

NS_NFE = "http://www.portalfiscal.inf.br/nfe"
AUTORIZADAS = {"100", "150"}
DUPLICADAS = {"204", "539"}
CANCELADAS = {"135", "155"}
INUTILIZADA = "102"

_BASE = {
    True: "https://homologacao.nfce.fazenda.sp.gov.br/ws/",
    False: "https://nfce.fazenda.sp.gov.br/ws/",
}


class SefazNfceErro(Exception):
    def __init__(self, mensagem: str, *, cstat: str = ""):
        super().__init__(mensagem)
        self.cstat = cstat


def _url(homologacao: bool, servico: str) -> str:
    return f"{_BASE[homologacao]}{servico}.asmx"


def _local(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def _texto(pai, nome: str) -> str:
    for filho in pai.iter():
        if _local(filho.tag) == nome and (filho.text or "").strip():
            return filho.text.strip()
    return ""


def ler_retorno(xml_bytes: bytes) -> dict:
    """Lê o protocolo quando a SEFAZ devolveu um. Sem protocolo, fica o cStat do lote."""
    root = ET.fromstring(xml_bytes)
    inf = None
    for no in root.iter():
        if _local(no.tag) == "infProt":
            inf = no
            break
    alvo = inf if inf is not None else root
    return {
        "cstat": _texto(alvo, "cStat"),
        "motivo": _texto(alvo, "xMotivo"),
        "chave": _texto(alvo, "chNFe"),
        "protocolo": _texto(alvo, "nProt"),
    }


def _postar(url: str, acao: str, corpo: str, key_pem: bytes, cert_pem: bytes) -> dict:
    try:
        bruto = postar_soap(url, acao, envelope_soap(_operacao(acao), _namespace(acao), corpo), key_pem, cert_pem)
    except SefazNfeErro as exc:
        raise SefazNfceErro(str(exc).replace("na consulta da NF-e", "na NFC-e")) from exc
    except Exception as exc:
        raise SefazNfceErro("A SEFAZ não respondeu a NFC-e.") from exc
    return ler_retorno(bruto)


def _operacao(acao: str) -> str:
    return acao.rsplit("/", 1)[-1]


def _namespace(acao: str) -> str:
    return acao.rsplit("/", 1)[0]


def enviar_lote(xml_envio: str, *, homologacao: bool, key_pem: bytes, cert_pem: bytes) -> dict:
    acao = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4/nfeAutorizacaoLote"
    return _postar(_url(homologacao, "NFeAutorizacao4"), acao, xml_envio, key_pem, cert_pem)


def consultar_chave(chave: str, *, homologacao: bool, key_pem: bytes, cert_pem: bytes) -> dict:
    ambiente = "2" if homologacao else "1"
    corpo = (
        f'<consSitNFe xmlns="{NS_NFE}" versao="4.00">'
        f"<tpAmb>{ambiente}</tpAmb><xServ>CONSULTAR</xServ><chNFe>{chave}</chNFe></consSitNFe>"
    )
    acao = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeConsultaProtocolo4/nfeConsultaNF"
    return _postar(_url(homologacao, "NFeConsultaProtocolo4"), acao, corpo, key_pem, cert_pem)


def enviar_evento(evento_xml: str, *, homologacao: bool, key_pem: bytes, cert_pem: bytes) -> dict:
    corpo = f'<envEvento xmlns="{NS_NFE}" versao="1.00"><idLote>1</idLote>{evento_xml}</envEvento>'
    acao = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4/nfeRecepcaoEvento"
    return _postar(_url(homologacao, "NFeRecepcaoEvento4"), acao, corpo, key_pem, cert_pem)


def enviar_inutilizacao(inutilizacao_xml: str, *, homologacao: bool, key_pem: bytes, cert_pem: bytes) -> dict:
    acao = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeInutilizacao4/nfeInutilizacaoNF"
    return _postar(_url(homologacao, "NFeInutilizacao4"), acao, inutilizacao_xml, key_pem, cert_pem)


def certificado_da_clinica(pfx: bytes, senha: str) -> tuple[bytes, bytes]:
    try:
        return pem_do_pfx(pfx, senha)
    except Exception as exc:
        raise SefazNfceErro("O certificado A1 da clínica não pôde ser lido. Confira a senha em Nota Fiscal.") from exc
