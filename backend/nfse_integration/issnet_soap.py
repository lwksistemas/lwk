"""Envelope SOAP e utilitários HTTP para ISSNet."""
import re
from xml.sax.saxutils import escape as xml_escape


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


def montar_soap_envelope_xsd_string(nome_operacao: str, dados_xml: str) -> str:
    dados = strip_xml_declaration(dados_xml or "")
    cabec_raw = (
        '<cabecalho versao="2.04" xmlns="http://www.abrasf.org.br/nfse.xsd">'
        '<versaoDados>2.04</versaoDados>'
        '</cabecalho>'
    )
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
        'xmlns:nfse="http://nfse.abrasf.org.br">'
        '<soap:Header/>'
        '<soap:Body>'
        f'<nfse:{nome_operacao}>'
        f'<nfseCabecMsg>{xml_escape(cabec_raw)}</nfseCabecMsg>'
        f'<nfseDadosMsg>{xml_escape(dados)}</nfseDadosMsg>'
        f'</nfse:{nome_operacao}>'
        '</soap:Body>'
        '</soap:Envelope>'
    )


def montar_soap_envelope_aninhado(nome_operacao: str, dados_xml: str) -> str:
    dados = strip_xml_declaration(dados_xml or "")
    cabec_txt = (
        '<cabecalho versao="2.04" xmlns="http://www.abrasf.org.br/nfse.xsd">'
        '<versaoDados>2.04</versaoDados>'
        '</cabecalho>'
    )
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
        'xmlns:nfse="http://nfse.abrasf.org.br">'
        '<soap:Header/>'
        '<soap:Body>'
        f'<nfse:{nome_operacao}>'
        f'<nfseCabecMsg>{cabec_txt}</nfseCabecMsg>'
        f'<nfseDadosMsg>{dados}</nfseDadosMsg>'
        f'</nfse:{nome_operacao}>'
        '</soap:Body>'
        '</soap:Envelope>'
    )


def montar_soap_envelope_cdata(nome_operacao: str, dados_xml: str) -> str:
    dados = strip_xml_declaration(dados_xml or "")
    cabec_txt = (
        '<cabecalho versao="2.04" xmlns="http://www.abrasf.org.br/nfse.xsd">'
        '<versaoDados>2.04</versaoDados>'
        '</cabecalho>'
    )
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
        'xmlns:nfse="http://nfse.abrasf.org.br">'
        '<soap:Header/>'
        '<soap:Body>'
        f'<nfse:{nome_operacao}>'
        f'<nfseCabecMsg>{cdata_section(cabec_txt)}</nfseCabecMsg>'
        f'<nfseDadosMsg>{cdata_section(dados)}</nfseDadosMsg>'
        f'</nfse:{nome_operacao}>'
        '</soap:Body>'
        '</soap:Envelope>'
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
