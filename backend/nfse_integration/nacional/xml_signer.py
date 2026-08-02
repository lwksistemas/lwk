"""Assinatura digital XML (XMLDSIG) para NFS-e Nacional.

Padrão: XML Digital Signature (https://www.w3.org/TR/xmldsig-core/)
Algoritmo: RSA-SHA1 (padrão legado) ou RSA-SHA256 (Nacional v1.01)
Certificado: ICP-Brasil A1 ou A3 (.pfx/.p12)
"""
import contextlib
import logging
import os
import tempfile

from lxml import etree

logger = logging.getLogger(__name__)

DSIG_NS = "http://www.w3.org/2000/09/xmldsig#"


def _known_issuer_cert_url(issuer_name: str) -> str | None:
    """Fallback com URLs diretas de intermediárias ICP-Brasil (ITI)."""
    name = (issuer_name or "").lower()
    if "soluti multipla v5 g2" in name:
        return "https://acraiz.icpbrasil.gov.br/credenciadas/SOLUTI/v5/AC_SOLUTI_Multipla_v5_G2.crt"
    if "soluti multipla v5" in name:
        return "https://acraiz.icpbrasil.gov.br/credenciadas/SOLUTI/v5/AC_SOLUTI_Multipla_v5.crt"
    if "soluti multipla" in name:
        return "https://acraiz.icpbrasil.gov.br/credenciadas/SOLUTI/v2/AC_Soluti_Multipla_v1.crt"
    return None


def _aia_ca_issuer_urls(cert):
    """Extrai URLs HTTP(S) da extensão AIA (caIssuers)."""
    from cryptography import x509

    urls = []
    try:
        for ext in cert.extensions:
            if ext.oid != x509.ExtensionOID.AUTHORITY_INFORMATION_ACCESS:
                continue
            for access in ext.value:
                if access.access_method != x509.AuthorityInformationAccessOID.CA_ISSUERS:
                    continue
                loc = access.access_location
                # cryptography representa URI como UniformResourceIdentifier.value
                value = getattr(loc, "value", None)
                if value and isinstance(value, str):
                    url = value
                elif value is not None:
                    url = str(value)
                else:
                    url = str(loc)
                if url.lower().startswith(("http://", "https://")):
                    urls.append(url)
    except Exception as e:
        logger.debug("Erro ao ler AIA do certificado: %s", e)
    return urls


def _load_certs_from_response(content: bytes, url: str) -> list:
    """Carrega um ou mais certificados de resposta DER, PEM ou PKCS#7."""
    from cryptography import x509
    from cryptography.hazmat.primitives.serialization import pkcs7

    # Tenta como certificado único DER
    try:
        return [x509.load_der_x509_certificate(content)]
    except Exception:
        pass

    # Tenta como PEM (uma ou mais certs)
    try:
        text = content.decode("ascii", errors="ignore")
        pem_blocks = [
            block + "-----END CERTIFICATE-----"
            for block in text.split("-----BEGIN CERTIFICATE-----")[1:]
        ]
        certs = [x509.load_pem_x509_certificate(block.encode("ascii")) for block in pem_blocks]
        if certs:
            logger.info("PEM: extraídos %d certificado(s) de %s", len(certs), url)
            return list(certs)
    except Exception:
        pass

    # Tenta como PKCS#7 (.p7b)
    try:
        certs = pkcs7.load_der_pkcs7_certificates(content)
        if certs:
            logger.info("PKCS#7: extraídos %d certificado(s) de %s", len(certs), url)
            return list(certs)
    except Exception as e:
        logger.debug("Não foi possível interpretar %s como DER/PEM/PKCS#7: %s", url, e)
    return []


def _completar_cadeia_certificados(cert_obj, extra_certs):
    """Tenta montar a cadeia ICP-Brasil usando certificados do PFX, AIA e fallback ITI."""
    from cryptography import x509

    chain = []
    seen = set()

    def add_cert(cert):
        if cert and cert.serial_number not in seen:
            chain.append(cert)
            seen.add(cert.serial_number)

    add_cert(cert_obj)
    if extra_certs:
        for c in extra_certs:
            add_cert(c)

    import requests

    # 1) Seguir extensão AIA para baixar intermediários que faltem
    current = cert_obj
    for depth in range(5):
        if not current or current.issuer == current.subject:
            break
        urls = _aia_ca_issuer_urls(current)
        if not urls:
            logger.info("AIA: nenhuma URL caIssuers HTTP(S) encontrada no certificado (profundidade %d)", depth)
            break
        next_cert = None
        for url in urls:
            logger.info("AIA: tentando baixar intermediário de %s", url)
            try:
                r = requests.get(url, timeout=15)
                r.raise_for_status()
                certs = _load_certs_from_response(r.content, url)
                for issuer_cert in certs:
                    if issuer_cert.serial_number not in seen:
                        logger.info("AIA: intermediário baixado com sucesso (serial %s)", issuer_cert.serial_number)
                        add_cert(issuer_cert)
                        next_cert = issuer_cert
                if next_cert:
                    break
            except Exception as e:
                logger.warning("AIA: falha ao baixar intermediário de %s: %s", url, e)
        if not next_cert:
            break
        current = next_cert

    # 2) Fallback por nome do emissor, caso AIA falhe ou não tenha sido suficiente
    last = chain[-1] if chain else cert_obj
    if last and last.issuer != last.subject:
        issuer_name = last.issuer.rfc4514_string()
        fallback_url = _known_issuer_cert_url(issuer_name)
        if fallback_url and fallback_url not in [u for u in _aia_ca_issuer_urls(last)]:
            logger.info("Fallback ICP-Brasil: tentando baixar intermediário de %s", fallback_url)
            try:
                r = requests.get(fallback_url, timeout=15)
                r.raise_for_status()
                certs = _load_certs_from_response(r.content, fallback_url)
                for issuer_cert in certs:
                    if issuer_cert.serial_number not in seen:
                        logger.info("Fallback: intermediário baixado com sucesso (serial %s)", issuer_cert.serial_number)
                        add_cert(issuer_cert)
            except Exception as e:
                logger.warning("Fallback: falha ao baixar intermediário de %s: %s", fallback_url, e)

    return chain


def _adicionar_certificados_x509(
    x509_data,
    cert_obj,
    extra_certs=None,
    incluir_cadeia: bool = True,
):
    """Remove certificados X509Data existentes e adiciona folha + intermediários."""
    from cryptography.hazmat.primitives.serialization import Encoding

    existing = x509_data.findall(f"{{{DSIG_NS}}}X509Certificate")
    for cert in existing:
        x509_data.remove(cert)

    if incluir_cadeia:
        certs = _completar_cadeia_certificados(cert_obj, extra_certs or [])
    else:
        certs = [cert_obj]
    logger.info("Incluindo %d certificado(s) na X509Data", len(certs))

    for cert in certs:
        pem_b64 = cert.public_bytes(Encoding.PEM).decode("ascii")
        # remove PEM headers/footers e junta linhas
        lines = [line.strip() for line in pem_b64.splitlines() if line and not line.startswith("--")]
        cert_el = etree.SubElement(x509_data, f"{{{DSIG_NS}}}X509Certificate")
        cert_el.text = "".join(lines)


def carregar_certificado_pfx(pfx_path: str, senha: str) -> tuple:
    """Carrega chave privada e certificado de um arquivo .pfx/.p12.

    Returns:
        Tuple (private_key, certificate, extra_certs)

    """
    from cryptography.hazmat.primitives.serialization import pkcs12

    with open(pfx_path, "rb") as f:
        pfx_data = f.read()

    private_key, certificate, extra = pkcs12.load_key_and_certificates(
        pfx_data, senha.encode(),
    )
    if certificate is None:
        raise ValueError("O arquivo .pfx não contém certificado válido.")
    if private_key is None:
        raise ValueError("O arquivo .pfx não contém chave privada.")

    return private_key, certificate, extra


def carregar_certificado_bytes(pfx_bytes: bytes, senha: str) -> tuple:
    """Carrega certificado a partir de bytes (para uso com BinaryField do Django).
    """
    from cryptography.hazmat.primitives.serialization import pkcs12

    private_key, certificate, extra = pkcs12.load_key_and_certificates(
        pfx_bytes, senha.encode(),
    )
    if certificate is None:
        raise ValueError("Os bytes do certificado não contêm certificado válido.")
    if private_key is None:
        raise ValueError("Os bytes do certificado não contêm chave privada.")

    return private_key, certificate, extra


def assinar_xml_dps(
    xml_str: str,
    pfx_path: str,
    senha_pfx: str,
    prefixo_ds: bool = True,
    usar_cadeia: bool = True,
) -> str:
    """Assina o XML da DPS com certificado digital.

    A assinatura é feita no elemento infDPS (Reference URI = #Id do infDPS).
    Usa enveloped signature com Canonicalization C14N e RSA-SHA1.

    Args:
        xml_str: XML da DPS como string
        pfx_path: Caminho para o arquivo .pfx
        senha_pfx: Senha do certificado
        prefixo_ds: se False, usa namespace padrão sem prefixo ds:
        usar_cadeia: se False, inclui apenas o certificado folha na X509Data

    Returns:
        XML assinado como string

    """
    import xmlsec

    root = etree.fromstring(xml_str.encode("utf-8"))

    # Carregar chave privada, certificado folha e cadeia intermediária
    private_key, cert_obj, extra_certs = carregar_certificado_pfx(pfx_path, senha_pfx)

    from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat

    key_pem = private_key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())
    cert_pem = cert_obj.public_bytes(Encoding.PEM)

    # Criar chave xmlsec
    key = xmlsec.Key.from_memory(key_pem, xmlsec.constants.KeyDataFormatPem)
    key.load_cert_from_memory(cert_pem, xmlsec.constants.KeyDataFormatPem)

    # Completar cadeia ICP-Brasil (AIA + fallback) para X509Data
    chain = _completar_cadeia_certificados(cert_obj, extra_certs)
    logger.info("Cadeia de certificados montada: %d certificado(s) (folha + intermediários)", len(chain))

    # Encontrar o elemento infDPS e seu Id
    ns = "http://www.sped.fazenda.gov.br/nfse"
    inf_dps = root.find(f"{{{ns}}}infDPS")
    if inf_dps is None:
        raise ValueError("Elemento infDPS não encontrado no XML")

    inf_id = inf_dps.get("Id")
    if not inf_id:
        raise ValueError("Atributo Id não encontrado em infDPS")

    # Criar template de assinatura
    # Signature como último filho do root (DPS)
    # Usar RSA-SHA1 conforme Portal Contribuinte (nfse.gov.br)
    ns_prefix = "ds" if prefixo_ds else None
    sig_node = xmlsec.template.create(
        root,
        xmlsec.constants.TransformInclC14N,
        xmlsec.constants.TransformRsaSha1,
        ns=ns_prefix,
    )
    root.append(sig_node)

    # Reference apontando para o infDPS via URI=#Id
    ref = xmlsec.template.add_reference(
        sig_node,
        xmlsec.constants.TransformSha1,
        uri=f"#{inf_id}",
    )
    xmlsec.template.add_transform(ref, xmlsec.constants.TransformEnveloped)
    xmlsec.template.add_transform(ref, xmlsec.constants.TransformInclC14N)

    # KeyInfo com X509Data (certificado folha ou cadeia completa)
    key_info = xmlsec.template.ensure_key_info(sig_node)
    x509_data = xmlsec.template.add_x509_data(key_info)
    xmlsec.template.x509_data_add_certificate(x509_data)
    _adicionar_certificados_x509(x509_data, cert_obj, chain, incluir_cadeia=usar_cadeia)

    # Garante que o atributo Id seja reconhecido como ID do documento
    xmlsec.tree.add_ids(root, ["Id"])

    sign_ctx = xmlsec.SignatureContext()
    sign_ctx.key = key
    sign_ctx.register_id(inf_dps, "Id", None)
    sign_ctx.sign(sig_node)

    # Verificação local com chave pública do certificado folha.
    verify_key = xmlsec.Key.from_memory(cert_pem, xmlsec.constants.KeyDataFormatCertPem)
    verify_ctx = xmlsec.SignatureContext()
    verify_ctx.key = verify_key
    verify_ctx.register_id(inf_dps, "Id", None)
    xmlsec.tree.add_ids(root, ["Id"])
    try:
        verify_ctx.verify(sig_node)
        logger.info("Assinatura verificada localmente com sucesso (Reference=#%s).", inf_id)
    except Exception as e:
        logger.error("Falha na verificação local da assinatura (Reference=#%s): %s", inf_id, e)
        raise

    result = '<?xml version="1.0" encoding="UTF-8"?>' + etree.tostring(root, encoding="unicode", xml_declaration=False)
    logger.info("XML DPS assinado com sucesso (RSA-SHA1, Reference=#%s)", inf_id)
    return result


def assinar_xml_dps_bytes(
    xml_str: str,
    pfx_bytes: bytes,
    senha_pfx: str,
    prefixo_ds: bool = True,
    usar_cadeia: bool = True,
) -> str:
    """Assina XML da DPS usando certificado em bytes (BinaryField).
    Cria arquivo temporário e delega para assinar_xml_dps.
    """
    cert_path = None
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pfx")  # noqa: SIM115
        tmp.write(pfx_bytes)
        tmp.close()
        cert_path = tmp.name

        return assinar_xml_dps(
            xml_str, cert_path, senha_pfx,
            prefixo_ds=prefixo_ds, usar_cadeia=usar_cadeia,
        )
    finally:
        if cert_path:
            with contextlib.suppress(OSError):
                os.unlink(cert_path)


def _carregar_chave_xmlsec(pfx_path: str, senha_pfx: str):
    import xmlsec
    from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat

    private_key, cert_obj, extra_certs = carregar_certificado_pfx(pfx_path, senha_pfx)

    # Confirma que o certificado pertence à chave privada
    if private_key.public_key().public_numbers() != cert_obj.public_key().public_numbers():
        raise ValueError("Chave privada e certificado do .pfx não formam um par válido.")

    key_pem = private_key.private_bytes(
        Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption(),
    )
    cert_pem = cert_obj.public_bytes(Encoding.PEM)
    key = xmlsec.Key.from_memory(key_pem, xmlsec.constants.KeyDataFormatPem)
    key.load_cert_from_memory(cert_pem, xmlsec.constants.KeyDataFormatCertPem)
    return key, cert_obj, extra_certs


def _assinar_elemento_por_id(
    parent_el,
    target_el,
    key,
    ref_id: str,
    cert_obj=None,
    extra_certs=None,
    prefixo_ds: bool = True,
    usar_cadeia: bool = True,
    usar_sha256: bool = False,
) -> None:
    """Assinatura enveloped no parent, Reference URI=#ref_id apontando para target_el."""
    import xmlsec
    from cryptography.hazmat.primitives.serialization import Encoding

    # Evita Signature duplicada em reprocessamento
    for child in list(parent_el):
        if etree.QName(child.tag).localname == "Signature":
            parent_el.remove(child)

    ns_prefix = "ds" if prefixo_ds else None
    if usar_sha256:
        sig_transform = xmlsec.constants.TransformRsaSha256
        digest_transform = xmlsec.constants.TransformSha256
    else:
        sig_transform = xmlsec.constants.TransformRsaSha1
        digest_transform = xmlsec.constants.TransformSha1
    sig_node = xmlsec.template.create(
        parent_el,
        xmlsec.constants.TransformInclC14N,
        sig_transform,
        ns=ns_prefix,
    )
    parent_el.append(sig_node)
    ref = xmlsec.template.add_reference(
        sig_node,
        digest_transform,
        uri=f"#{ref_id}",
    )
    xmlsec.template.add_transform(ref, xmlsec.constants.TransformEnveloped)
    xmlsec.template.add_transform(ref, xmlsec.constants.TransformInclC14N)
    key_info = xmlsec.template.ensure_key_info(sig_node)
    x509_data = xmlsec.template.add_x509_data(key_info)
    xmlsec.template.x509_data_add_certificate(x509_data)
    if cert_obj is not None:
        _adicionar_certificados_x509(x509_data, cert_obj, extra_certs, incluir_cadeia=usar_cadeia)

    # Garante que o atributo Id seja reconhecido como ID do documento
    # tanto para assinar quanto para verificar a referência.
    root_el = target_el.getroottree().getroot()
    xmlsec.tree.add_ids(root_el, ["Id"])

    sign_ctx = xmlsec.SignatureContext()
    sign_ctx.key = key
    sign_ctx.register_id(target_el, "Id", None)
    sign_ctx.sign(sig_node)

    # Verificação local com chave pública do certificado folha.
    cert_pem = cert_obj.public_bytes(Encoding.PEM) if cert_obj else b""
    verify_key = xmlsec.Key.from_memory(cert_pem, xmlsec.constants.KeyDataFormatCertPem)
    verify_ctx = xmlsec.SignatureContext()
    verify_ctx.key = verify_key
    verify_ctx.register_id(target_el, "Id", None)
    xmlsec.tree.add_ids(root_el, ["Id"])
    try:
        verify_ctx.verify(sig_node)
        logger.info("Assinatura verificada localmente com sucesso (Reference=#%s).", ref_id)
    except Exception as e:
        logger.error("Falha na verificação local da assinatura (Reference=#%s): %s", ref_id, e)
        raise


def assinar_xml_enviar_lote_dps(
    xml_str: str,
    pfx_path: str,
    senha_pfx: str,
    assinar_lote: bool = True,
    prefixo_ds: bool = True,
    usar_cadeia: bool = True,
    usar_sha256: bool = False,
) -> str:
    """Assina EnviarLoteDpsSincronoEnvio / EnviarLoteDpsEnvio (padrão Nacional ISSNet).

    1) Assina cada DPS (Reference=#Id do infDPS)
    2) Opcionalmente assina o LoteDps (Reference=#Id do lote). O ISSNet Nacional
       rejeita quando a segunda assinatura está presente, então o default pode
       ser desligado pelo chamador.
    3) prefixo_ds=False emite <Signature xmlns="..."> sem prefixo ds:, conforme
       exemplos do ISSNet Nacional.
    4) usar_cadeia=False inclui apenas o certificado folha na X509Data, conforme
       exemplos do ISSNet Nacional.
    """
    ns = "http://www.sped.fazenda.gov.br/nfse"
    root = etree.fromstring(xml_str.encode("utf-8"))
    root_local = etree.QName(root.tag).localname if root.tag else ""

    if root_local in ("DPS",):
        return assinar_xml_dps(xml_str, pfx_path, senha_pfx)

    key, cert_obj, extra_certs = _carregar_chave_xmlsec(pfx_path, senha_pfx)

    # Completa a cadeia ICP-Brasil (AIA + fallback) para incluir no X509Data
    chain = _completar_cadeia_certificados(cert_obj, extra_certs)
    logger.info("Cadeia de certificados montada: %d certificado(s) (folha + intermediários)", len(chain))

    dps_nodes = root.findall(f".//{{{ns}}}DPS")
    if not dps_nodes:
        raise ValueError("Nenhum elemento DPS encontrado para assinatura no lote Nacional.")

    for dps in dps_nodes:
        inf_dps = dps.find(f"{{{ns}}}infDPS")
        if inf_dps is None:
            raise ValueError("Elemento infDPS não encontrado em DPS do lote.")
        inf_id = (inf_dps.get("Id") or "").strip()
        if not inf_id:
            raise ValueError("Atributo Id ausente em infDPS.")
        _assinar_elemento_por_id(
            dps, inf_dps, key, inf_id, cert_obj, chain,
            prefixo_ds=prefixo_ds, usar_cadeia=usar_cadeia,
            usar_sha256=usar_sha256,
        )

    # Signature do lote fica na raiz (irmã de LoteDps), Reference=#Id do LoteDps
    if assinar_lote:
        lote = root.find(f"{{{ns}}}LoteDps")
        if lote is not None and root_local in ("EnviarLoteDpsSincronoEnvio", "EnviarLoteDpsEnvio"):
            lote_id = (lote.get("Id") or "").strip()
            if not lote_id:
                num = lote.findtext(f"{{{ns}}}NumeroLote") or "1"
                lote_id = f"Lote{num}"
                lote.set("Id", lote_id)
            _assinar_elemento_por_id(
                root, lote, key, lote_id, cert_obj, chain,
                prefixo_ds=prefixo_ds, usar_cadeia=usar_cadeia,
            )

    result = etree.tostring(root, encoding="unicode", xml_declaration=False)
    logger.info(
        "XML lote DPS assinado (%s): %d DPS%s",
        root_local or "?",
        len(dps_nodes),
        " + assinatura do envio" if assinar_lote else "",
    )
    return result


def extrair_info_certificado(pfx_path: str, senha: str) -> dict:
    """Extrai informações do certificado para exibição.

    Returns:
        Dict com subject, issuer, valid_from, valid_to, cnpj

    """
    _, cert_obj, _ = carregar_certificado_pfx(pfx_path, senha)


    subject = cert_obj.subject.rfc4514_string()
    issuer = cert_obj.issuer.rfc4514_string()

    # Tentar extrair CNPJ do subject (OID 2.16.76.1.3.3)
    cnpj = ""
    try:
        for attr in cert_obj.subject:
            if attr.oid.dotted_string == "2.16.76.1.3.3":
                cnpj = attr.value
                break
    except Exception:
        pass

    return {
        "subject": subject[:500],
        "issuer": issuer[:500],
        "valid_from": cert_obj.not_valid_before_utc.isoformat(),
        "valid_to": cert_obj.not_valid_after_utc.isoformat(),
        "cnpj": cnpj,
    }
