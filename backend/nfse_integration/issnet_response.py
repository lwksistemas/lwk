"""Parsers de resposta XML/SOAP do ISSNet."""
import contextlib
import re
from datetime import datetime
from typing import Any
from xml.sax.saxutils import escape as xml_escape

from lxml import etree

from nfse_integration.issnet_constants import NS_NFSE


def extrair_body_soap(soap_xml: str) -> str:
    try:
        root = etree.fromstring(soap_xml.encode("utf-8") if isinstance(soap_xml, str) else soap_xml)
        body = root.find(".//{http://schemas.xmlsoap.org/soap/envelope/}Body")
        if body is None:
            body = root.find(".//{http://www.w3.org/2003/05/soap-envelope}Body")
        if body is not None and len(body) > 0:
            first = body[0]
            tag = etree.QName(first.tag).localname if isinstance(first.tag, str) else ""
            if tag == "Fault":
                faultstring = first.findtext(
                    "{http://schemas.xmlsoap.org/soap/envelope/}faultstring", "",
                ) or first.findtext("faultstring", "")
                detail = first.findtext(
                    "{http://schemas.xmlsoap.org/soap/envelope/}detail", "",
                ) or first.findtext("detail", "")
                if not (detail or "").strip():
                    for el in first.iter():
                        if etree.QName(el.tag).localname == "detail":
                            detail = "".join(el.itertext()).strip()
                            break
                msg = faultstring or "Erro SOAP desconhecido"
                if (msg or "").strip().lower() == "error":
                    msg = (
                        "Erro genérico do webservice ISSNet (sem detail). "
                        "Verifique certificado mTLS, cadastro na prefeitura e XML (RPS/assinatura). "
                        "Se o mesmo RPS foi tentado várias vezes, confira no portal ISSNet o último "
                        "RPS aceito e atualize no CRM o campo «Último RPS conhecido»."
                    )
                if detail:
                    msg += f" - {detail}"
                return (
                    f'<ListaMensagemRetorno xmlns="{NS_NFSE}">'
                    f'<MensagemRetorno>'
                    f'<Codigo>SOAP</Codigo>'
                    f'<Mensagem>{xml_escape(msg)}</Mensagem>'
                    f'</MensagemRetorno>'
                    f'</ListaMensagemRetorno>'
                )
            for el in first.iter():
                if etree.QName(el.tag).localname == "outputXML":
                    inner = (el.text or "").strip()
                    if inner:
                        return inner
            return etree.tostring(first, encoding="unicode")
        return soap_xml
    except Exception:
        return soap_xml


def parse_resposta_xml(xml_str: str) -> dict[str, Any]:
    try:
        root = etree.fromstring(xml_str.encode("utf-8") if isinstance(xml_str, str) else xml_str)
    except etree.XMLSyntaxError:
        amostra = (xml_str or "")[:400].strip()
        amostra = " ".join(amostra.split())
        if amostra and not amostra.startswith("<"):
            return {
                "success": False,
                "error": (
                    "Resposta do ISSNet não é XML válido (provável indisponibilidade do serviço). "
                    f"{amostra}"
                ),
            }
        return {"success": False, "error": f"XML inválido na resposta do ISSNet: {amostra}"}

    nsmap = {"ns": NS_NFSE}
    msgs = root.findall(".//ns:MensagemRetorno", nsmap)
    if msgs:
        erros = []
        for msg in msgs:
            codigo = (msg.findtext("ns:Codigo", "", nsmap) or "").strip()
            mensagem = msg.findtext("ns:Mensagem", "", nsmap)
            correcao = msg.findtext("ns:Correcao", "", nsmap)
            texto = f"[{codigo}] {mensagem}"
            if correcao:
                texto += f" - {correcao}"
            if codigo.upper() == "E138":
                texto += (
                    " Em Ribeirao Preto (ISSNet), o codigo E138 costuma indicar falta de "
                    "autorizacao da prefeitura para emissao via webservice em producao para este CNPJ; "
                    "abra protocolo ou e-mail ao ISS municipal solicitando liberacao do ambiente de "
                    "integracao (conforme orientacao da prefeitura / Nota Control)."
                )
            erros.append(texto)
        return {"success": False, "error": "; ".join(erros)}

    nfse_el = root.find(".//ns:CompNfse/ns:Nfse/ns:InfNfse", nsmap)
    if nfse_el is None:
        nfse_el = root.find(".//ns:Nfse/ns:InfNfse", nsmap)
    if nfse_el is None:
        nfse_el = root.find(f".//{{{NS_NFSE}}}InfNfse")

    if nfse_el is not None:
        numero = nfse_el.findtext(f"{{{NS_NFSE}}}Numero", "")
        cod_ver = nfse_el.findtext(f"{{{NS_NFSE}}}CodigoVerificacao", "")
        dt_text = nfse_el.findtext(f"{{{NS_NFSE}}}DataEmissao", "")
        dt_emissao = datetime.now()
        if dt_text:
            with contextlib.suppress(Exception):
                dt_emissao = datetime.fromisoformat(dt_text.replace("Z", "+00:00"))
        return {
            "success": True,
            "numero_nf": numero,
            "codigo_verificacao": cod_ver,
            "data_emissao": dt_emissao,
            "xml_nfse": xml_str,
        }

    return {
        "success": False,
        "error": f"NFS-e nao encontrada na resposta: {xml_str[:500]}",
    }


def parse_consultar_url_nfse_resposta(xml_str: str) -> dict[str, Any]:
    """Extrai número, RPS e URL de ConsultarUrlNfseResposta (ListaLinks)."""
    if not (xml_str or "").strip():
        return {"success": False, "error": "Resposta vazia do ConsultarUrlNfse."}
    try:
        root = etree.fromstring(xml_str.encode("utf-8") if isinstance(xml_str, str) else xml_str)
    except etree.XMLSyntaxError as exc:
        return {"success": False, "error": f"XML inválido na resposta do ConsultarUrlNfse: {exc}"}

    ns = NS_NFSE
    for links in root.iter(f"{{{ns}}}Links"):
        numero = (
            links.findtext(f".//{{{ns}}}IdentificacaoNfse/{{{ns}}}Numero", "")
            or links.findtext(f".//{{{ns}}}Numero", "")
            or ""
        ).strip()
        if not numero:
            continue
        rps_txt = links.findtext(f".//{{{ns}}}IdentificacaoRps/{{{ns}}}Numero", "") or ""
        url = (
            links.findtext(f".//{{{ns}}}UrlVisualizacaoNfse", "")
            or links.findtext(f".//{{{ns}}}UrlNfse", "")
            or ""
        ).strip()
        out: dict[str, Any] = {
            "success": True,
            "numero_nf": numero,
            "url": url,
        }
        if (rps_txt or "").strip().isdigit():
            out["numero_rps"] = int((rps_txt or "").strip())
        return out

    return parse_resposta_xml(xml_str)


def parse_resposta_xml_nfse_por_numero(xml_str: str, numero_nf: str) -> dict[str, Any]:
    """Extrai CompNfse/InfNfse da resposta quando há lista (consulta por número/faixa)."""
    alvo = str(numero_nf or "").strip()
    if not alvo or not (xml_str or "").strip():
        return {"success": False, "error": "Resposta vazia ou número da NFS-e não informado."}
    try:
        root = etree.fromstring(xml_str.encode("utf-8") if isinstance(xml_str, str) else xml_str)
    except etree.XMLSyntaxError as exc:
        return {"success": False, "error": f"XML inválido na resposta do ISSNet: {exc}"}

    ns = NS_NFSE
    for inf in root.iter(f"{{{ns}}}InfNfse"):
        numero = (inf.findtext(f"{{{ns}}}Numero", "") or "").strip()
        if numero != alvo:
            continue
        cod_ver = inf.findtext(f"{{{ns}}}CodigoVerificacao", "")
        dt_text = inf.findtext(f"{{{ns}}}DataEmissao", "")
        dt_emissao = datetime.now()
        if dt_text:
            with contextlib.suppress(Exception):
                dt_emissao = datetime.fromisoformat(dt_text.replace("Z", "+00:00"))
        comp = inf
        for anc in inf.iterancestors():
            if etree.QName(anc.tag).localname == "CompNfse":
                comp = anc
                break
        xml_nfse = etree.tostring(comp, encoding="unicode")
        return {
            "success": True,
            "numero_nf": numero,
            "codigo_verificacao": cod_ver,
            "data_emissao": dt_emissao,
            "xml_nfse": xml_nfse,
        }
    return parse_resposta_xml(xml_str)


def extrair_detalhes_nfse_xml(xml_str: str) -> dict[str, Any]:
    """Extrai tomador, valores e descrição do XML ABRASF (consulta/recuperação)."""
    out: dict[str, Any] = {}
    if not (xml_str or "").strip():
        return out
    try:
        root = etree.fromstring(xml_str.encode("utf-8") if isinstance(xml_str, str) else xml_str)
    except etree.XMLSyntaxError:
        return out

    ns = NS_NFSE
    inf = root.find(f".//{{{ns}}}InfNfse")
    if inf is None:
        return out

    out["valor"] = inf.findtext(f"{{{ns}}}Servico/{{{ns}}}Valores/{{{ns}}}ValorServicos", "") or ""
    out["aliquota_iss"] = inf.findtext(f"{{{ns}}}Servico/{{{ns}}}Valores/{{{ns}}}Aliquota", "") or ""
    out["valor_iss"] = inf.findtext(f"{{{ns}}}Servico/{{{ns}}}Valores/{{{ns}}}ValorIss", "") or ""
    out["servico_descricao"] = (
        inf.findtext(f"{{{ns}}}Servico/{{{ns}}}Discriminacao", "")
        or inf.findtext(f"{{{ns}}}Servico/{{{ns}}}ItemListaServico", "")
        or ""
    )
    tomador = inf.find(f".//{{{ns}}}TomadorServico")
    if tomador is not None:
        out["tomador_nome"] = (
            tomador.findtext(f"{{{ns}}}RazaoSocial", "")
            or tomador.findtext(f".//{{{ns}}}RazaoSocial", "")
            or ""
        )
        cpf = tomador.findtext(f".//{{{ns}}}Cpf", "") or ""
        cnpj = tomador.findtext(f".//{{{ns}}}Cnpj", "") or ""
        out["tomador_cpf_cnpj"] = cnpj or cpf or ""
    id_rps = inf.find(f".//{{{ns}}}IdentificacaoRps/{{{ns}}}Numero")
    if id_rps is not None and (id_rps.text or "").strip().isdigit():
        out["numero_rps"] = int((id_rps.text or "").strip())
    return out


def extrair_erros(texto: str) -> str:
    erros = re.findall(r"<Mensagem>(.*?)</Mensagem>", texto)
    return "; ".join(erros) if erros else texto[:500]


def parse_resposta_cancelamento(xml_str: str) -> dict[str, Any]:
    texto = (xml_str or "").strip()
    if not texto:
        return {"success": False, "error": "Resposta vazia do ISSNet no cancelamento."}

    if re.search(r"<\s*Fault\b", texto, re.IGNORECASE):
        return {
            "success": False,
            "error": (
                "Erro genérico do webservice ISSNet no cancelamento. "
                "Tente novamente ou sincronize o status da nota."
            ),
        }

    try:
        root = etree.fromstring(texto.encode("utf-8"))
    except etree.XMLSyntaxError:
        amostra = " ".join(texto[:400].split())
        return {"success": False, "error": f"XML inválido na resposta do cancelamento: {amostra}"}

    nsmap = {"ns": NS_NFSE}
    msgs = root.findall(".//ns:MensagemRetorno", nsmap)
    if not msgs:
        msgs = root.findall(".//MensagemRetorno")

    if msgs:
        erros = []
        for msg in msgs:
            codigo = (msg.findtext("ns:Codigo", "", nsmap) or msg.findtext("Codigo") or "").strip()
            mensagem = msg.findtext("ns:Mensagem", "", nsmap) or msg.findtext("Mensagem") or ""
            correcao = msg.findtext("ns:Correcao", "", nsmap) or msg.findtext("Correcao") or ""
            texto_erro = f"[{codigo}] {mensagem}".strip()
            if correcao:
                texto_erro += f" - {correcao}"
            if codigo.upper() == "E206":
                texto_erro += (
                    " Para “Erro na emissão”, a prefeitura exige substituição de NFS-e "
                    "(não cancelamento via webservice). Use o motivo 2 (Serviço não prestado) "
                    "ou cancele/substitua no portal ISSNet."
                )
            erros.append(texto_erro)
        return {"success": False, "error": "; ".join(erros)}

    if re.search(
        r"<\s*(Cancelamento|CancelarNfseResposta|NfseCancelada|ConfirmacaoCancelamento)\b",
        texto,
        re.IGNORECASE,
    ):
        return {"success": True, "message": "NFS-e cancelada com sucesso no ISSNet"}

    if re.search(r"DataHoraCancelamento|DataHora\s*Cancelamento", texto, re.IGNORECASE):
        return {"success": True, "message": "NFS-e cancelada com sucesso no ISSNet"}

    return {
        "success": False,
        "error": f"Cancelamento não confirmado na resposta do ISSNet: {texto[:500]}",
    }


def interpretar_cancelamento(parsed: dict[str, Any], xml_body: str) -> dict[str, Any]:
    especifico = parse_resposta_cancelamento(xml_body or "")
    if especifico.get("success"):
        return especifico
    if especifico.get("error") and "MensagemRetorno" in (xml_body or ""):
        return especifico
    err = str((parsed or {}).get("error") or "")
    if parsed and parsed.get("success") is False and "NFS-e nao encontrada na resposta" in err:
        return especifico
    return parsed or especifico
