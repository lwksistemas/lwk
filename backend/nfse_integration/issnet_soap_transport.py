"""Transporte SOAP/mTLS para o webservice ISSNet (Zeep + POST manual)."""
import logging
import re
import time
from typing import Any

import requests as req

from nfse_integration.issnet_cert import certificado_mtls_temporario
from nfse_integration.issnet_constants import CABEC_MSG
from nfse_integration.issnet_response import extrair_body_soap, parse_resposta_xml
from nfse_integration.issnet_soap import (
    issnet_corpo_parece_xml,
    issnet_decodificar_corpo,
    issnet_fault_soap_generico,
    montar_soap_envelope_aninhado,
    montar_soap_envelope_cdata,
    montar_soap_envelope_xsd_string,
    strip_xml_declaration,
)

logger = logging.getLogger(__name__)

# Configuração de retry
MAX_RETRIES = 2  # Tentativas extras além da primeira
RETRY_BACKOFF_SECONDS = [2.0, 4.0]  # Espera entre tentativas (backoff crescente)
RETRYABLE_EXCEPTIONS = (
    req.exceptions.ConnectionError,
    req.exceptions.ChunkedEncodingError,
    req.exceptions.ReadTimeout,
    req.exceptions.ConnectTimeout,
    ConnectionResetError,
    OSError,
)

ZEEP_OPERACOES_MTLS = frozenset({
    "RecepcionarLoteRps",
    "RecepcionarLoteRpsSincrono",
    "ConsultarLoteRps",
    "ConsultarUrlNfse",
    "CancelarNfse",
    "ConsultarNfsePorRps",
    "ConsultarNfseServicoPrestado",
    "ConsultarNfsePorFaixa",
})


def criar_soap_client(wsdl_url: str, base_url: str, cert_path: str | None = None, key_path: str | None = None):
    """Cliente Zeep; com cert_path/key_path habilita mTLS na sessão requests."""
    from requests import Session
    from zeep import Client
    from zeep.transports import Transport

    session = Session()
    session.headers.update({"User-Agent": "LWK-Sistemas/CRM"})
    if cert_path and key_path:
        session.cert = (cert_path, key_path)
        session.headers["User-Agent"] = "LWK-Sistemas/CRM (ISSNet ABRASF 2.04)"
    transport = Transport(session=session, timeout=30 if not cert_path else 25)
    client = Client(wsdl_url, transport=transport)
    for service in client.wsdl.services.values():
        for port in service.ports.values():
            port.binding_options["address"] = base_url
    return client


def zeep_chamar_com_mtls(
    wsdl_url: str,
    base_url: str,
    nome_operacao: str,
    dados_xml: str,
    cert_path: str,
    key_path: str,
    timeout_s: int = 25,
):
    """Uma chamada SOAP via Zeep com certificado cliente (mTLS)."""
    client = criar_soap_client(wsdl_url, base_url, cert_path, key_path)
    op = getattr(client.service, nome_operacao, None)
    if op is None:
        raise AttributeError(f"Operacao {nome_operacao!r} nao existe no WSDL ISSNet")
    dados = strip_xml_declaration(dados_xml or "")
    with client.settings(raw_response=True, strict=False):
        return op(nfseCabecMsg=CABEC_MSG, nfseDadosMsg=dados)


def post_soap_operacao(
    *,
    base_url: str,
    wsdl_url: str,
    certificado_path: str,
    senha_certificado: str,
    nome_operacao: str,
    soap_action_uri: str,
    dados_xml: str,
) -> tuple[dict[str, Any], str]:
    """POST SOAP 1.1 com mTLS; tenta Zeep primeiro, depois envelopes manuais.
    Inclui retry com backoff exponencial para erros de rede/timeout.
    Retorna (parsed_dict, xml_body).
    """
    logger.debug("ISSNet %s SOAPAction=%s", nome_operacao, soap_action_uri)

    last_error = None
    for attempt in range(1 + MAX_RETRIES):
        try:
            result = _post_soap_operacao_inner(
                base_url=base_url,
                wsdl_url=wsdl_url,
                certificado_path=certificado_path,
                senha_certificado=senha_certificado,
                nome_operacao=nome_operacao,
                soap_action_uri=soap_action_uri,
                dados_xml=dados_xml,
            )
            return result
        except RETRYABLE_EXCEPTIONS as e:
            last_error = e
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF_SECONDS[attempt] if attempt < len(RETRY_BACKOFF_SECONDS) else 4.0
                logger.warning(
                    "ISSNet %s tentativa %d/%d falhou (%s); retry em %.1fs",
                    nome_operacao, attempt + 1, 1 + MAX_RETRIES, type(e).__name__, wait,
                )
                time.sleep(wait)
            else:
                logger.error("ISSNet %s todas as %d tentativas falharam: %s", nome_operacao, 1 + MAX_RETRIES, e)

    return {"success": False, "error": f"Erro de conexão após {1 + MAX_RETRIES} tentativas: {last_error}"}, ""


def _post_soap_operacao_inner(
    *,
    base_url: str,
    wsdl_url: str,
    certificado_path: str,
    senha_certificado: str,
    nome_operacao: str,
    soap_action_uri: str,
    dados_xml: str,
) -> tuple[dict[str, Any], str]:
    """Implementação interna do POST SOAP (sem retry — chamada pelo wrapper)."""
    try:
        with certificado_mtls_temporario(certificado_path, senha_certificado) as (cert_path, key_path):
            http_timeout = (8, 20)

            if nome_operacao in ZEEP_OPERACOES_MTLS:
                try:
                    rz = zeep_chamar_com_mtls(
                        wsdl_url,
                        base_url,
                        nome_operacao,
                        dados_xml,
                        cert_path,
                        key_path,
                        timeout_s=http_timeout[1],
                    )
                    txt_z = (getattr(rz, "text", None) or "") if rz is not None else ""
                    sc = getattr(rz, "status_code", None)
                    logger.info(
                        "ISSNet %s zeep+mTLS HTTP %s, preview: %s",
                        nome_operacao,
                        sc,
                        txt_z[:400],
                    )
                    if (sc is not None and sc >= 400) or "Fault" in txt_z:
                        logger.error("ISSNet zeep+mTLS resposta (ate 8000 chars): %s", txt_z[:8000])
                    if issnet_corpo_parece_xml(txt_z) and not issnet_fault_soap_generico(txt_z):
                        xml_body = extrair_body_soap(txt_z)
                        return parse_resposta_xml(xml_body), xml_body
                    logger.warning(
                        "ISSNet %s zeep+mTLS sem sucesso (Fault generico ou resposta nao parseavel); "
                        "tentando POST manual",
                        nome_operacao,
                    )
                except Exception as e:
                    logger.warning("ISSNet %s zeep+mTLS: %s — tentando POST manual", nome_operacao, e)

            return _post_soap_manual(
                base_url=base_url,
                nome_operacao=nome_operacao,
                soap_action_uri=soap_action_uri,
                dados_xml=dados_xml,
                cert_path=cert_path,
                key_path=key_path,
                http_timeout=http_timeout,
            )
    except RETRYABLE_EXCEPTIONS:
        raise  # Propagar para o wrapper de retry
    except Exception as e:
        logger.exception("Erro ao enviar SOAP: %s", e)
        return {"success": False, "error": str(e)}, ""


def _post_soap_manual(
    *,
    base_url: str,
    nome_operacao: str,
    soap_action_uri: str,
    dados_xml: str,
    cert_path: str,
    key_path: str,
    http_timeout: tuple[int, int],
) -> tuple[dict[str, Any], str]:
    def _headers(content_type: str) -> dict:
        return {
            "Content-Type": content_type,
            "SOAPAction": f'"{soap_action_uri}"',
            "Connection": "close",
            "Accept": "text/xml",
            "User-Agent": "LWK-Sistemas/CRM (ISSNet ABRASF 2.04)",
        }

    if nome_operacao == "ConsultarNfsePorRps":
        strategies = (
            (
                montar_soap_envelope_aninhado(nome_operacao, dados_xml),
                _headers("application/soap+xml; charset=utf-8"),
                "XML aninhado + application/soap+xml (PHP)",
            ),
            (
                montar_soap_envelope_cdata(nome_operacao, dados_xml),
                _headers("text/xml; charset=utf-8"),
                "CDATA + text/xml",
            ),
            (
                montar_soap_envelope_xsd_string(nome_operacao, dados_xml),
                _headers("text/xml; charset=utf-8"),
                "xsd:string (XML escapado) + text/xml",
            ),
        )
    else:
        strategies = (
            (
                montar_soap_envelope_aninhado(nome_operacao, dados_xml),
                _headers("application/soap+xml; charset=utf-8"),
                "XML aninhado + application/soap+xml (PHP)",
            ),
            (
                montar_soap_envelope_cdata(nome_operacao, dados_xml),
                _headers("text/xml; charset=utf-8"),
                "CDATA + text/xml",
            ),
            (
                montar_soap_envelope_xsd_string(nome_operacao, dados_xml),
                _headers("text/xml; charset=utf-8"),
                "xsd:string (XML escapado) + text/xml",
            ),
        )

    def _do_post(soap_body: str, hdrs: dict):
        return req.post(
            base_url,
            data=soap_body.encode("utf-8"),
            headers=hdrs,
            timeout=http_timeout,
            cert=(cert_path, key_path),
        )

    r = None
    for strat_idx, (soap_try, headers_try, label) in enumerate(strategies):
        logger.info(
            "ISSNet SOAP %s (~%d bytes, %s) com mTLS",
            nome_operacao,
            len(soap_try.encode("utf-8")),
            label,
        )
        try:
            r = _do_post(soap_try, headers_try)
        except (
            req.exceptions.ConnectionError,
            req.exceptions.ChunkedEncodingError,
            req.exceptions.ReadTimeout,
        ) as e:
            logger.warning("ISSNet SOAP POST: erro de conexao, uma nova tentativa: %s", e)
            time.sleep(1.5)
            r = _do_post(soap_try, headers_try)

        logger.info(
            "Resposta ISSNet HTTP %s, preview: %s",
            r.status_code,
            (r.text or "")[:500],
        )
        if r.status_code >= 400 or "Fault" in (r.text or ""):
            logger.error("ISSNet resposta (ate 8000 chars): %s", (r.text or "")[:8000])

        if r.status_code in (502, 503, 504) and not issnet_corpo_parece_xml(r.text or ""):
            logger.warning(
                "ISSNet HTTP %s sem XML; repetindo POST uma vez apos 2s",
                r.status_code,
            )
            time.sleep(2.0)
            r = _do_post(soap_try, headers_try)
            logger.info(
                "Resposta ISSNet HTTP %s (apos retry), preview: %s",
                r.status_code,
                (r.text or "")[:500],
            )

        if r.status_code in (502, 503, 504) and not issnet_corpo_parece_xml(r.text or ""):
            msg = issnet_decodificar_corpo(r).strip() or "(sem corpo)"
            msg = " ".join(msg.split())
            return (
                {
                    "success": False,
                    "error": (
                        f"Servico ISSNet indisponivel (HTTP {r.status_code}). "
                        f"Tente novamente em instantes. {msg[:400]}"
                    ),
                },
                "",
            )

        if (
            nome_operacao == "ConsultarNfsePorRps"
            and strat_idx < len(strategies) - 1
            and re.search(r"<\s*Codigo\s*>\s*E160\s*<\s*/\s*Codigo\s*>", (r.text or ""), re.IGNORECASE)
        ):
            logger.warning(
                "ISSNet %s retornou E160 (schema) com %r; tentando formato alternativo",
                nome_operacao,
                label,
            )
            continue

        if not (
            issnet_corpo_parece_xml(r.text or "")
            and issnet_fault_soap_generico(r.text or "")
        ):
            break
        if strat_idx >= len(strategies) - 1:
            break
        logger.warning(
            "ISSNet Fault generico com estrategia %r; tentando formato alternativo",
            label,
        )

    if not issnet_corpo_parece_xml(r.text or ""):
        msg = issnet_decodificar_corpo(r).strip() or "(resposta vazia)"
        msg = " ".join(msg.split())
        return (
            {
                "success": False,
                "error": (
                    f"O webservice ISSNet respondeu HTTP {r.status_code} sem XML "
                    f"(serviço indisponível ou erro no balanceador). {msg[:600]}"
                ),
            },
            "",
        )

    xml_body = extrair_body_soap(r.text)
    return parse_resposta_xml(xml_body), xml_body
