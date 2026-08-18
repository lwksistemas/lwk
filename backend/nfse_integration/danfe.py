"""Helpers para obter a URL oficial da DANFE/NFS-e."""
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

URL_INVALID_MARKERS = ("xmlsoap", "w3.org", "schemas.", "abrasf")

# URL base do portal ISSNet Nacional Ribeirão Preto para visualização de NFS-e
ISSNET_NACIONAL_PORTAL_RP = "https://nfse.issnetonline.com.br/ribeiraopreto/rps/visualizarnfse.aspx"


def url_danfe_valida(url: str | None) -> bool:
    """Retorna True quando a URL parece ser do portal/PDF, nao de schema SOAP."""
    if not url or not str(url).startswith("http"):
        return False
    return not any(marker in str(url) for marker in URL_INVALID_MARKERS)


def _extrair_prestador_do_xml(xml_nfse: str) -> tuple[str, str]:
    cnpj = ""
    inscricao_municipal = ""

    if xml_nfse:
        cnpj_match = (
            re.search(r"<Cnpj>(\d+)</Cnpj>", xml_nfse, re.IGNORECASE)
            or re.search(r"<CNPJ>(\d+)</CNPJ>", xml_nfse)
        )
        im_match = (
            re.search(r"<InscricaoMunicipal>(\d+)</InscricaoMunicipal>", xml_nfse, re.IGNORECASE)
            or re.search(r"<IM>(\d+)</IM>", xml_nfse)
        )
        if cnpj_match:
            cnpj = cnpj_match.group(1)
        if im_match:
            inscricao_municipal = im_match.group(1)

    return cnpj, inscricao_municipal


def _salvar_pdf_url(nfse: Any, url: str) -> None:
    if not nfse or not url:
        return

    try:
        nfse.pdf_url = url[:1000]
        nfse.save(update_fields=["pdf_url"])
    except Exception as exc:
        logger.debug("Nao foi possivel salvar pdf_url da NFS-e id=%s: %s", getattr(nfse, "id", None), exc)


def _config_usa_padrao_nacional(config: Any | None) -> bool:
    from nfse_integration.issnet_shared import usar_issnet_padrao_nacional

    return usar_issnet_padrao_nacional(config)


def url_xml_download_from_danfe(url_danfe: str) -> str:
    """Deriva o link de download do XML a partir da URL da DANFE ISSNet RP."""
    url = (url_danfe or "").strip()
    if not url:
        return ""
    if "Nota_Digital_Nacional.aspx" in url:
        return url.replace("Nota_Digital_Nacional.aspx", "NotaDigitalXmlDownload.aspx")
    if "NotaDigital.aspx" in url:
        return url.replace("NotaDigital.aspx", "NotaDigitalXmlDownload.aspx")
    return ""


def _url_xml_download_from_danfe(url_danfe: str) -> str:
    """Alias legado — use url_xml_download_from_danfe."""
    return url_xml_download_from_danfe(url_danfe)


def obter_url_visualizacao_nfse_loja(
    nfse: Any,
    loja: Any,
    loja_id: int,
) -> str:
    """URL oficial para visualizar/baixar a NFS-e (portal da prefeitura ou provedor).
    Mesma fonte usada no e-mail ao tomador — não usa PDF interno do sistema.
    """
    pdf_url = (getattr(nfse, "pdf_url", "") or "").strip()
    if url_danfe_valida(pdf_url):
        return pdf_url

    provedor = (getattr(nfse, "provedor", "") or "issnet").strip().lower()
    if provedor == "issnet":
        return buscar_url_danfe_issnet(nfse, loja_id=loja_id, loja=loja)
    return ""


def _resolver_cnpj_im_danfe(config, loja, nfse) -> tuple[str, str]:
    """Resolve (cnpj_prestador, im_prestador) para busca de DANFE ISSNet."""
    cnpj_prestador = getattr(config, "cnpj_prestador", "") or ""
    if not cnpj_prestador and loja is not None:
        cnpj_prestador = re.sub(r"\D", "", getattr(loja, "cpf_cnpj", "") or "")
    im_prestador = (
        getattr(config, "inscricao_municipal", "")
        or getattr(loja, "inscricao_municipal", "")
        or ""
    )
    # Se a config carregada veio sem IM (ex.: registro duplicado vazio),
    # tenta a outra CRMConfig da mesma loja com IM preenchida.
    if not str(im_prestador or "").strip() and config is not None:
        try:
            from crm_vendas.models_config import CRMConfig

            loja_id = getattr(config, "loja_id", None) or getattr(loja, "id", None)
            if loja_id:
                alt = (
                    CRMConfig.objects.filter(loja_id=loja_id)
                    .exclude(inscricao_municipal__isnull=True)
                    .exclude(inscricao_municipal="")
                    .order_by("id")
                    .first()
                )
                if alt and (alt.inscricao_municipal or "").strip():
                    im_prestador = alt.inscricao_municipal
                    if not cnpj_prestador:
                        cnpj_prestador = getattr(alt, "cnpj_prestador", "") or cnpj_prestador
        except Exception as exc:
            logger.debug("Fallback IM CRMConfig: %s", exc)

    xml_nfse = getattr(nfse, "xml_nfse", "") if nfse else ""
    xml_cnpj, xml_im = _extrair_prestador_do_xml(xml_nfse)
    return xml_cnpj or cnpj_prestador, xml_im or im_prestador


def buscar_url_danfe_issnet(
    nfse: Any | None = None,
    *,
    numero_nf: str = "",
    loja_id: int | None = None,
    loja: Any | None = None,
    config: Any | None = None,
    salvar: bool = True,
) -> str:
    """Consulta o ISSNet para obter a URL oficial da DANFE.

    Pode receber uma instancia de NFSe ja persistida ou apenas numero/config
    para caminhos onde a nota acabou de ser emitida.
    """
    numero_nf = numero_nf or getattr(nfse, "numero_nf", "")
    if not numero_nf:
        return ""

    if nfse and getattr(nfse, "provedor", "") != "issnet":
        return ""

    pdf_url = getattr(nfse, "pdf_url", "") if nfse else ""
    if url_danfe_valida(pdf_url):
        return pdf_url

    try:
        if config is None:
            from crm_vendas.models_config import CRMConfig

            effective_loja_id = loja_id or getattr(nfse, "loja_id", None)
            if not effective_loja_id:
                return ""
            config = CRMConfig.get_or_create_for_loja(effective_loja_id)

        from nfse_integration.issnet_loja import (
            certificado_configurado_loja,
            issnet_client_loja,
        )

        if not certificado_configurado_loja(config):
            return ""

        # Nacional (DPS/RTC): ABRASF ConsultarUrlNfse NÃO enxerga essas notas.
        if _config_usa_padrao_nacional(config):
            url_nacional = _gerar_url_portal_issnet_nacional(
                nfse,
                loja,
                config=config,
                salvar=salvar,
                numero_nf=str(numero_nf),
            )
            if url_danfe_valida(url_nacional):
                return url_nacional
            # Fallback ABRASF: notas antigas (pré-Nacional) ainda podem responder.
            # Notas DPS costumam falhar aqui — só tenta se ainda não há URL.

        cnpj_prestador, im_prestador = _resolver_cnpj_im_danfe(config, loja, nfse)

        with issnet_client_loja(config, prefix="issnet_danfe_") as client:
            resultado = client.consultar_url_nfse(
                numero_nf=numero_nf,
                prestador_cnpj=cnpj_prestador,
                inscricao_municipal=im_prestador,
            )

        url = resultado.get("url") if resultado.get("success") else ""
        if not url_danfe_valida(url):
            return ""

        if salvar:
            _salvar_pdf_url(nfse, url)
        return url
    except Exception as exc:
        logger.warning("Erro ao buscar URL DANFE ISSNet: %s", exc)
        return ""


def buscar_url_danfe_issnet_superadmin(nfse: Any, config: Any | None = None, *, salvar: bool = True) -> str:
    """Consulta ISSNet usando configuracao global do superadmin (NFSeEmitida).
    """
    if not nfse or getattr(nfse, "provedor", "") != "issnet":
        return ""

    numero_nf = getattr(nfse, "numero_nf", "") or ""
    if not numero_nf:
        return ""

    pdf_url = getattr(nfse, "pdf_url", "") or ""
    if url_danfe_valida(pdf_url):
        return pdf_url

    try:
        if config is None:
            from asaas_integration.models_nfse_config import SuperadminNFSeConfig

            config = SuperadminNFSeConfig.get_config()

        from nfse_integration.issnet_superadmin import (
            certificado_configurado,
            issnet_client_superadmin,
        )

        if not certificado_configurado(config):
            return ""

        cnpj_prestador = getattr(config, "prestador_cnpj", "") or ""
        im_prestador = getattr(config, "prestador_inscricao_municipal", "") or ""
        xml_nfse = getattr(nfse, "xml_nfse", "") or ""
        xml_cnpj, xml_im = _extrair_prestador_do_xml(xml_nfse)
        cnpj_prestador = xml_cnpj or cnpj_prestador
        im_prestador = xml_im or im_prestador

        with issnet_client_superadmin(config, prefix="issnet_danfe_") as client:
            resultado = client.consultar_url_nfse(
                numero_nf=numero_nf,
                prestador_cnpj=cnpj_prestador,
                inscricao_municipal=im_prestador,
            )

        url = resultado.get("url") if resultado.get("success") else ""
        if not url_danfe_valida(url):
            return ""

        if salvar:
            try:
                nfse.pdf_url = (url or "").strip()
                nfse.save(update_fields=["pdf_url"])
            except Exception as exc:
                logger.debug(
                    "Nao foi possivel salvar pdf_url superadmin id=%s: %s",
                    getattr(nfse, "id", None),
                    exc,
                )
        return url
    except Exception as exc:
        logger.warning("Erro ao buscar URL DANFE ISSNet (superadmin): %s", exc)
        return ""


def _gerar_url_portal_issnet_nacional(
    nfse: Any,
    loja: Any,
    *,
    config: Any | None = None,
    salvar: bool = True,
    numero_nf: str = "",
) -> str:
    """Consulta URL da DANFE no webservice Nacional do ISSNet.

    Usa o endpoint ConsultarUrlNfse do Nacional (não ABRASF) para obter
    o link oficial da nota no portal notaeletronica.com.br
    (Nota_Digital_Nacional.aspx com token).
    """
    numero_nf = str(numero_nf or getattr(nfse, "numero_nf", "") or "").strip()
    if not numero_nf or not numero_nf.isdigit():
        return ""

    try:
        import contextlib

        from core.encryption import decrypt_value
        from crm_vendas.models_config import CRMConfig
        from nfse_integration.issnet_loja import certificado_configurado_loja
        from nfse_integration.issnet_nacional_client import ISSNetNacionalClient

        loja_id = getattr(nfse, "loja_id", None) if nfse is not None else None
        if not loja_id:
            loja_id = getattr(loja, "id", None)
        if not loja_id:
            return ""

        if config is None:
            config = CRMConfig.get_or_create_for_loja(loja_id)
        if not certificado_configurado_loja(config):
            return ""

        cert_bytes = getattr(config, "issnet_certificado", None) or getattr(
            config, "nacional_certificado", None,
        )
        senha = (
            getattr(config, "issnet_senha_certificado", "")
            or getattr(config, "nacional_senha_certificado", "")
            or ""
        )
        if senha:
            with contextlib.suppress(Exception):
                senha = decrypt_value(senha)

        cnpj, im = _resolver_cnpj_im_danfe(config, loja, nfse)
        cnpj = re.sub(r"\D", "", cnpj or "")
        im = re.sub(r"\D", "", im or "")
        if not cnpj or not im:
            logger.warning(
                "DANFE Nacional: CNPJ/IM ausentes para NFS-e %s (loja_id=%s)",
                numero_nf,
                loja_id,
            )
            return ""

        ambiente = (
            "homologacao"
            if getattr(config, "issnet_ambiente_homologacao", False)
            else "producao"
        )
        client = ISSNetNacionalClient(
            cert_bytes=bytes(cert_bytes) if cert_bytes else None,
            cert_password=senha,
            ambiente=ambiente,
            prestador_cnpj=cnpj,
            prestador_inscricao_municipal=im,
        )

        resultado = client.consultar_url_nfse(
            numero_nf,
            chave_acesso=(
                getattr(nfse, "codigo_verificacao", "") if nfse is not None else ""
            ) or "",
        )
        url = (resultado.get("url") or "").strip() if resultado.get("success") else ""
        if url_danfe_valida(url):
            if salvar and nfse is not None:
                _salvar_pdf_url(nfse, url)
                xml_url = url_xml_download_from_danfe(url)
                if xml_url:
                    try:
                        nfse.xml_url = xml_url[:1000]
                        nfse.save(update_fields=["xml_url"])
                    except Exception as exc:
                        logger.debug(
                            "Nao foi possivel salvar xml_url id=%s: %s",
                            getattr(nfse, "id", None),
                            exc,
                        )
            return url

        logger.warning(
            "DANFE Nacional: sem URL válida para NFS-e %s: %s",
            numero_nf,
            resultado.get("erro"),
        )

    except Exception as exc:
        logger.warning("Erro ao buscar URL DANFE Nacional: %s", exc)

    # O ConsultarUrlNfse do ISSNet Nacional de Ribeirão Preto retorna E160/E999
    # (serviço em construção). A URL real da DANFE usa um token criptografado
    # que só vem no e-mail automático do ISSNet ou na resposta do ConsultarUrlNfse
    # — não é possível gerá-lo a partir da chave de acesso.
    # O usuário deve colar o link do e-mail do ISSNet no ícone "colar link" da nota.

    return ""
