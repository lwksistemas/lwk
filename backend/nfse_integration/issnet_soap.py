"""Envelope SOAP e utilitários HTTP para ISSNet."""
import re
from xml.sax.saxutils import escape as xml_escape

from nfse_integration.issnet_constants import (
    CABEC_MSG,
    CABEC_MSG_NACIONAL,
    NS_NFSE_NACIONAL,
    NS_NFSE_WSDL,
)


def strip_xml_declaration(fragment: str) -> str:
    s = (fragment or "").strip()
    if s.startswith("<?xml"):
        s = re.sub(r"^\s*<\?xml[^>]*\?>\s*", "", s, count=1, flags=re.IGNORECASE)
    return s


def cdata_section(payload: str) -> str:
    s = payload or ""
    if "]]>" in s:
        s = s.replace("]]>", "]]]]><![CDATA[>")
    return f"<![CDATA[{s}]]>"


def _montar_soap_envelope(
    nome_operacao: str,
    dados_xml: str,
    *,
    cabec_txt: str,
    target_ns: str,
    modo: str,
) -> str:
    """Monta envelope SOAP Document/Literal wrapped (nfseCabecMsg + nfseDadosMsg)."""
    dados = strip_xml_declaration(dados_xml or "")
    if modo == "xsd_string":
        cabec_body = xml_escape(cabec_txt)
        dados_body = xml_escape(dados)
    elif modo == "cdata":
        cabec_body = cdata_section(cabec_txt)
        dados_body = cdata_section(dados)
    else:  # aninhado
        cabec_body = cabec_txt
        dados_body = dados
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
        f'xmlns:nfse="{target_ns}">'
        '<soap:Header/>'
        '<soap:Body>'
        f'<nfse:{nome_operacao}>'
        f'<nfseCabecMsg>{cabec_body}</nfseCabecMsg>'
        f'<nfseDadosMsg>{dados_body}</nfseDadosMsg>'
        f'</nfse:{nome_operacao}>'
        '</soap:Body>'
        '</soap:Envelope>'
    )


def montar_soap_envelope_xsd_string(nome_operacao: str, dados_xml: str) -> str:
    return _montar_soap_envelope(
        nome_operacao, dados_xml, cabec_txt=CABEC_MSG, target_ns=NS_NFSE_WSDL, modo="xsd_string",
    )


def montar_soap_envelope_aninhado(nome_operacao: str, dados_xml: str) -> str:
    return _montar_soap_envelope(
        nome_operacao, dados_xml, cabec_txt=CABEC_MSG, target_ns=NS_NFSE_WSDL, modo="aninhado",
    )


def montar_soap_envelope_cdata(nome_operacao: str, dados_xml: str) -> str:
    return _montar_soap_envelope(
        nome_operacao, dados_xml, cabec_txt=CABEC_MSG, target_ns=NS_NFSE_WSDL, modo="cdata",
    )


def montar_soap_envelope_nacional_xsd_string(nome_operacao: str, dados_xml: str) -> str:
    """Envelope Nacional (ACBr XmlToStr): cabec/dados como xsd:string escapados, NS SPED."""
    return _montar_soap_envelope(
        nome_operacao,
        dados_xml,
        cabec_txt=CABEC_MSG_NACIONAL,
        target_ns=NS_NFSE_NACIONAL,
        modo="xsd_string",
    )


def montar_soap_envelope_nacional_cdata(nome_operacao: str, dados_xml: str) -> str:
    return _montar_soap_envelope(
        nome_operacao,
        dados_xml,
        cabec_txt=CABEC_MSG_NACIONAL,
        target_ns=NS_NFSE_NACIONAL,
        modo="cdata",
    )


def montar_soap_envelope_nacional_aninhado(nome_operacao: str, dados_xml: str) -> str:
    return _montar_soap_envelope(
        nome_operacao,
        dados_xml,
        cabec_txt=CABEC_MSG_NACIONAL,
        target_ns=NS_NFSE_NACIONAL,
        modo="aninhado",
    )


def issnet_fault_soap_generico(texto: str) -> bool:
    t = texto or ""
    if "s:Client" not in t and "Client</faultcode>" not in t:
        return False
    return bool(re.search(r"<faultstring>\s*Error\s*</faultstring>", t, re.IGNORECASE))


def issnet_corpo_parece_xml(texto: str) -> bool:
    if not (texto or "").strip():
        return False
    return texto.lstrip().startswith("<")


def issnet_decodificar_corpo(resposta) -> str:
    raw = getattr(resposta, "content", None) or b""
    if not raw:
        return (getattr(resposta, "text", None) or "").strip()
    for enc in ("utf-8", "utf-8-sig", "iso-8859-1", "windows-1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")
