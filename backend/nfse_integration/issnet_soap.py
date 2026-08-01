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


def _serializar_conteudo(fragmento: str, modo: str) -> str:
    if modo == "xsd_string":
        return xml_escape(fragmento)
    if modo == "cdata":
        return cdata_section(fragmento)
    # aninhado: insere o XML literalmente
    return fragmento


def _montar_soap_envelope(
    nome_operacao: str,
    dados_xml: str,
    *,
    cabec_txt: str,
    target_ns: str,
    modo: str | None = None,
    modo_cabec: str | None = None,
    modo_dados: str | None = None,
    prefixar_mensagens: bool = False,
) -> str:
    """Monta envelope SOAP Document/Literal wrapped (nfseCabecMsg + nfseDadosMsg).

    Os modos podem ser informados separadamente (modo_cabec / modo_dados) ou
    em conjunto (modo). Isso permite, por exemplo, cabeçalho aninhado e dados
    em CDATA/xsd:string, o que evita herança de namespace na assinatura.

    Quando prefixar_mensagens=True, os parâmetros do corpo da operação são
    prefixados com o namespace nfse: (ex.: <nfse:nfseCabecMsg>), conforme
    algumas implementações ASMX da ISSNet esperam.
    """
    if modo is not None and (modo_cabec is not None or modo_dados is not None):
        raise ValueError("Use 'modo' ou 'modo_cabec'/'modo_dados', não ambos.")
    if modo is not None:
        modo_cabec = modo_dados = modo
    if modo_cabec is None or modo_dados is None:
        raise ValueError("modo ou ambos modo_cabec/modo_dados são obrigatórios.")

    dados = strip_xml_declaration(dados_xml or "")
    cabec_body = _serializar_conteudo(cabec_txt, modo_cabec)
    dados_body = _serializar_conteudo(dados, modo_dados)
    pfx = "nfse:" if prefixar_mensagens else ""
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
        f'xmlns:nfse="{target_ns}">'
        '<soap:Header/>'
        '<soap:Body>'
        f'<nfse:{nome_operacao}>'
        f'<{pfx}nfseCabecMsg>{cabec_body}</{pfx}nfseCabecMsg>'
        f'<{pfx}nfseDadosMsg>{dados_body}</{pfx}nfseDadosMsg>'
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
    # Remove BOM e espaços em branco antes de verificar
    return texto.lstrip("\ufeff").lstrip().startswith("<")


def issnet_erro_schema_ou_cabecalho(texto: str) -> bool:
    """Retorna True se a resposta indicar rejeição de schema ou cabeçalho XML."""
    t = (texto or "").lower()
    return any(
        marker in t
        for marker in (
            "xml schema",
            "cabeçalho",
            "cabecalho",
            "fora do padrão",
            "fora do padrao",
            "desacordo com o xml schema",
            "invalid namespace",
        )
    )


def issnet_erro_assinatura(texto: str) -> bool:
    """Retorna True se a resposta indicar rejeição específica da assinatura."""
    t = (texto or "").lower()
    return any(
        marker in t
        for marker in (
            "erro na assinatura",
            "erro na assinatura",
            "assinatura",
            "signature",
            "digestvalue",
        )
    )


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
