"""Consulta NF-e de fornecedor na SEFAZ (Distribuição DFe) e ciência da operação.

A SEFAZ entrega primeiro um resumo. A ciência libera o XML completo com os produtos.
"""
from __future__ import annotations

import base64
import gzip
import logging
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo

import defusedxml.ElementTree as ET
import requests
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    pkcs12,
)

logger = logging.getLogger(__name__)

NS_NFE = "http://www.portalfiscal.inf.br/nfe"
URL_DIST = {
    False: "https://www1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    True: "https://hom1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
}
URL_EVENTO = {
    False: "https://www.nfe.fazenda.gov.br/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx",
    True: "https://hom.nfe.fazenda.gov.br/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx",
}
ACAO_DIST = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe/nfeDistDFeInteresse"
ACAO_EVENTO = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4/nfeRecepcaoEvento"
CIENCIA = "210210"
CSTAT_DOCUMENTOS = "138"
CSTAT_VAZIO = "137"
CSTAT_CONSUMO = "656"
CSTAT_EVENTO_OK = {"135", "136", "573"}

UF_IBGE = {
    "AC": "12", "AL": "27", "AM": "13", "AP": "16", "BA": "29", "CE": "23",
    "DF": "53", "ES": "32", "GO": "52", "MA": "21", "MG": "31", "MS": "50",
    "MT": "51", "PA": "15", "PB": "25", "PE": "26", "PI": "22", "PR": "41",
    "RJ": "33", "RN": "24", "RO": "11", "RR": "14", "RS": "43", "SC": "42",
    "SE": "28", "SP": "35", "TO": "17",
}


class SefazNfeErro(Exception):
    def __init__(self, mensagem: str, *, consumo_indevido: bool = False):
        super().__init__(mensagem)
        self.consumo_indevido = consumo_indevido


def codigo_uf(sigla: str) -> str:
    codigo = UF_IBGE.get((sigla or "").strip().upper(), "")
    if not codigo:
        raise SefazNfeErro("Informe a UF da loja para consultar as notas na SEFAZ.")
    return codigo


def _local(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def _texto(el, nome: str) -> str:
    for filho in el.iter():
        if _local(filho.tag) == nome and (filho.text or "").strip():
            return (filho.text or "").strip()
    return ""


def decodificar_doc_zip(conteudo_b64: str) -> bytes:
    bruto = base64.b64decode(conteudo_b64)
    return gzip.decompress(bruto)


def interpretar_ret_dist(xml_bytes: bytes) -> dict:
    """Lê retDistDFeInt. documentos traz schema, nsu e o XML descompactado."""
    root = ET.fromstring(xml_bytes)
    ret = None
    for el in root.iter():
        if _local(el.tag) == "retDistDFeInt":
            ret = el
            break
    if ret is None:
        raise SefazNfeErro("A SEFAZ não devolveu a distribuição de NF-e.")
    c_stat = _texto(ret, "cStat")
    motivo = _texto(ret, "xMotivo")
    if c_stat == CSTAT_CONSUMO:
        raise SefazNfeErro(motivo or "A SEFAZ pediu para aguardar antes de uma nova consulta.", consumo_indevido=True)
    documentos = []
    for doc in ret.iter():
        if _local(doc.tag) != "docZip":
            continue
        try:
            xml_doc = decodificar_doc_zip((doc.text or "").strip())
        except Exception:
            logger.warning("docZip da NF-e não pôde ser lido")
            continue
        documentos.append({
            "nsu": doc.attrib.get("NSU") or "",
            "schema": doc.attrib.get("schema") or "",
            "xml": xml_doc,
        })
    return {
        "c_stat": c_stat,
        "motivo": motivo,
        "ult_nsu": (_texto(ret, "ultNSU") or "0").zfill(15),
        "max_nsu": (_texto(ret, "maxNSU") or "0").zfill(15),
        "documentos": documentos,
        "vazio": c_stat == CSTAT_VAZIO,
    }


def classificar_documento(xml_doc: bytes) -> dict | None:
    """Separa resumo, XML completo ou documento que não é nota de produto."""
    root = ET.fromstring(xml_doc)
    raiz = _local(root.tag)
    if raiz == "resNFe":
        chave = _texto(root, "chNFe")
        if len(chave) != 44:
            return None
        return {
            "tipo": "resumo",
            "chave": chave,
            "emitente_documento": _texto(root, "CNPJ") or _texto(root, "CPF"),
            "fornecedor_nome": _texto(root, "xNome"),
            "data_emissao": (_texto(root, "dhEmi") or "")[:10],
            "valor": _texto(root, "vNF"),
            "tp_nf": _texto(root, "tpNF"),
        }
    if raiz in {"nfeProc", "NFe"}:
        from .estoque_xml_import_service import parse_nfe_xml

        parsed = parse_nfe_xml(xml_doc)
        if not parsed.get("chave"):
            return None
        return {"tipo": "completo", "parsed": parsed, "xml": xml_doc}
    return None


def xml_dist_nsu(*, cnpj: str, uf: str, ult_nsu: str, homologacao: bool) -> str:
    ambiente = "2" if homologacao else "1"
    nsu = "".join(c for c in (ult_nsu or "0") if c.isdigit()).zfill(15)[-15:]
    return (
        f'<distDFeInt xmlns="{NS_NFE}" versao="1.01">'
        f"<tpAmb>{ambiente}</tpAmb>"
        f"<cUFAutor>{codigo_uf(uf)}</cUFAutor>"
        f"<CNPJ>{cnpj}</CNPJ>"
        f"<distNSU><ultNSU>{nsu}</ultNSU></distNSU>"
        f"</distDFeInt>"
    )


def xml_evento_ciencia(*, cnpj: str, chave: str, homologacao: bool, agora: datetime | None = None) -> str:
    momento = agora or datetime.now(ZoneInfo("America/Sao_Paulo"))
    dh = momento.strftime("%Y-%m-%dT%H:%M:%S%z")
    dh = f"{dh[:-2]}:{dh[-2:]}"
    ambiente = "2" if homologacao else "1"
    ident = f"ID{CIENCIA}{chave}01"
    return (
        f'<evento xmlns="{NS_NFE}" versao="1.00">'
        f'<infEvento Id="{ident}">'
        f"<cOrgao>91</cOrgao>"
        f"<tpAmb>{ambiente}</tpAmb>"
        f"<CNPJ>{cnpj}</CNPJ>"
        f"<chNFe>{chave}</chNFe>"
        f"<dhEvento>{dh}</dhEvento>"
        f"<tpEvento>{CIENCIA}</tpEvento>"
        f"<nSeqEvento>1</nSeqEvento>"
        f"<verEvento>1.00</verEvento>"
        f'<detEvento versao="1.00"><descEvento>Ciencia da Operacao</descEvento></detEvento>'
        f"</infEvento></evento>"
    )


def assinar_evento(evento_xml: str, key_pem: bytes, cert_pem: bytes) -> str:
    from lxml import etree
    from signxml import XMLSigner, methods

    evento = etree.fromstring(evento_xml.encode("utf-8"))
    inf = next(el for el in evento if _local(el.tag) == "infEvento")
    signer = XMLSigner(
        method=methods.enveloped,
        signature_algorithm="rsa-sha256",
        digest_algorithm="sha256",
        c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
    )
    assinado = signer.sign(evento, key=key_pem, cert=cert_pem, reference_uri=f"#{inf.get('Id')}", id_attribute="Id")
    return etree.tostring(assinado, encoding="unicode")


def envelope_soap(operacao: str, namespace: str, corpo: str) -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">'
        f'<soap12:Body><{operacao} xmlns="{namespace}">'
        f"<nfeDadosMsg>{corpo}</nfeDadosMsg>"
        f"</{operacao}></soap12:Body></soap12:Envelope>"
    )


def pem_do_pfx(pfx: bytes, senha: str) -> tuple[bytes, bytes]:
    chave, certificado, _extra = pkcs12.load_key_and_certificates(pfx, (senha or "").encode("utf-8"))
    if chave is None or certificado is None:
        raise SefazNfeErro("O certificado A1 da clínica não contém chave privada.")
    key_pem = chave.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    cert_pem = certificado.public_bytes(Encoding.PEM)
    return key_pem, cert_pem


def postar_soap(url: str, acao: str, envelope: str, key_pem: bytes, cert_pem: bytes, timeout: int = 40) -> bytes:
    with tempfile.NamedTemporaryFile() as cert_file, tempfile.NamedTemporaryFile() as key_file:
        cert_file.write(cert_pem)
        cert_file.flush()
        key_file.write(key_pem)
        key_file.flush()
        resposta = requests.post(
            url,
            data=envelope.encode("utf-8"),
            headers={"Content-Type": f'application/soap+xml; charset=utf-8; action="{acao}"'},
            cert=(cert_file.name, key_file.name),
            timeout=timeout,
        )
    if resposta.status_code >= 400:
        raise SefazNfeErro(f"A SEFAZ respondeu {resposta.status_code} na consulta da NF-e.")
    return resposta.content


def consultar_distribuicao(*, cnpj: str, uf: str, ult_nsu: str, homologacao: bool, key_pem: bytes, cert_pem: bytes) -> dict:
    corpo = xml_dist_nsu(cnpj=cnpj, uf=uf, ult_nsu=ult_nsu, homologacao=homologacao)
    envelope = envelope_soap("nfeDistDFeInteresse", "http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe", corpo)
    bruto = postar_soap(URL_DIST[homologacao], ACAO_DIST, envelope, key_pem, cert_pem)
    return interpretar_ret_dist(bruto)


def enviar_ciencia(*, cnpj: str, chave: str, homologacao: bool, key_pem: bytes, cert_pem: bytes) -> bool:
    evento = assinar_evento(xml_evento_ciencia(cnpj=cnpj, chave=chave, homologacao=homologacao), key_pem, cert_pem)
    corpo = f'<envEvento xmlns="{NS_NFE}" versao="1.00"><idLote>1</idLote>{evento}</envEvento>'
    envelope = envelope_soap("nfeRecepcaoEvento", "http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4", corpo)
    bruto = postar_soap(URL_EVENTO[homologacao], ACAO_EVENTO, envelope, key_pem, cert_pem)
    root = ET.fromstring(bruto)
    c_stat = ""
    for el in root.iter():
        if _local(el.tag) == "cStat" and (el.text or "").strip():
            c_stat = el.text.strip()
            if c_stat in CSTAT_EVENTO_OK:
                return True
    return c_stat in CSTAT_EVENTO_OK
