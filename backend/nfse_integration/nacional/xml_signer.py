"""Assinatura digital XML (XMLDSIG) para NFS-e Nacional.

Padrão: XML Digital Signature (https://www.w3.org/TR/xmldsig-core/)
Algoritmo: RSA-SHA1 (conforme Portal Contribuinte nfse.gov.br)
Certificado: ICP-Brasil A1 ou A3 (.pfx/.p12)
"""
import contextlib
import logging
import os
import tempfile

from lxml import etree

logger = logging.getLogger(__name__)

DSIG_NS = "http://www.w3.org/2000/09/xmldsig#"


def _adicionar_certificados_x509(x509_data, cert_obj, extra_certs):
    """Adiciona certificado folha e eventuais intermediários ao X509Data.

    Alguns servidores (ex: ISSNet Nacional) não conseguem validar a assinatura
    sem a cadeia completa do certificado ICP-Brasil.
    """
    from cryptography.hazmat.primitives.serialization import Encoding

    existing = x509_data.findall(f"{{{DSIG_NS}}}X509Certificate")
    for cert in existing:
        x509_data.remove(cert)

    certs = [cert_obj]
    if extra_certs:
        certs.extend(extra_certs)

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


def assinar_xml_dps(xml_str: str, pfx_path: str, senha_pfx: str) -> str:
    """Assina o XML da DPS com certificado digital.

    A assinatura é feita no elemento infDPS (Reference URI = #Id do infDPS).
    Usa enveloped signature com Canonicalization C14N e RSA-SHA256.

    Args:
        xml_str: XML da DPS como string
        pfx_path: Caminho para o arquivo .pfx
        senha_pfx: Senha do certificado

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
    sig_node = xmlsec.template.create(
        root,
        xmlsec.constants.TransformInclC14N,
        xmlsec.constants.TransformRsaSha1,
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

    # KeyInfo com X509Data (certificado + cadeia completa)
    key_info = xmlsec.template.ensure_key_info(sig_node)
    x509_data = xmlsec.template.add_x509_data(key_info)
    xmlsec.template.x509_data_add_certificate(x509_data)
    _adicionar_certificados_x509(x509_data, cert_obj, extra_certs)

    # Assinar
    ctx = xmlsec.SignatureContext()
    ctx.key = key
    ctx.register_id(inf_dps, "Id", None)
    ctx.sign(sig_node)

    result = '<?xml version="1.0" encoding="UTF-8"?>' + etree.tostring(root, encoding="unicode", xml_declaration=False)
    logger.info("XML DPS assinado com sucesso (RSA-SHA1, Reference=#%s)", inf_id)
    return result


def assinar_xml_dps_bytes(xml_str: str, pfx_bytes: bytes, senha_pfx: str) -> str:
    """Assina XML da DPS usando certificado em bytes (BinaryField).
    Cria arquivo temporário e delega para assinar_xml_dps.
    """
    cert_path = None
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pfx")  # noqa: SIM115
        tmp.write(pfx_bytes)
        tmp.close()
        cert_path = tmp.name

        return assinar_xml_dps(xml_str, cert_path, senha_pfx)
    finally:
        if cert_path:
            with contextlib.suppress(OSError):
                os.unlink(cert_path)


def _carregar_chave_xmlsec(pfx_path: str, senha_pfx: str):
    import xmlsec
    from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat

    private_key, cert_obj, extra_certs = carregar_certificado_pfx(pfx_path, senha_pfx)
    key_pem = private_key.private_bytes(
        Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption(),
    )
    cert_pem = cert_obj.public_bytes(Encoding.PEM)
    key = xmlsec.Key.from_memory(key_pem, xmlsec.constants.KeyDataFormatPem)
    key.load_cert_from_memory(cert_pem, xmlsec.constants.KeyDataFormatPem)
    return key, cert_obj, extra_certs


def _assinar_elemento_por_id(parent_el, target_el, key, ref_id: str, cert_obj=None, extra_certs=None) -> None:
    """Assinatura enveloped no parent, Reference URI=#ref_id apontando para target_el."""
    import xmlsec

    # Evita Signature duplicada em reprocessamento
    for child in list(parent_el):
        if etree.QName(child.tag).localname == "Signature":
            parent_el.remove(child)

    sig_node = xmlsec.template.create(
        parent_el,
        xmlsec.constants.TransformInclC14N,
        xmlsec.constants.TransformRsaSha1,
    )
    parent_el.append(sig_node)
    ref = xmlsec.template.add_reference(
        sig_node,
        xmlsec.constants.TransformSha1,
        uri=f"#{ref_id}",
    )
    xmlsec.template.add_transform(ref, xmlsec.constants.TransformEnveloped)
    xmlsec.template.add_transform(ref, xmlsec.constants.TransformInclC14N)
    key_info = xmlsec.template.ensure_key_info(sig_node)
    x509_data = xmlsec.template.add_x509_data(key_info)
    xmlsec.template.x509_data_add_certificate(x509_data)
    if cert_obj is not None:
        _adicionar_certificados_x509(x509_data, cert_obj, extra_certs)

    ctx = xmlsec.SignatureContext()
    ctx.key = key
    ctx.register_id(target_el, "Id", None)
    ctx.sign(sig_node)


def assinar_xml_enviar_lote_dps(xml_str: str, pfx_path: str, senha_pfx: str) -> str:
    """Assina EnviarLoteDpsSincronoEnvio / EnviarLoteDpsEnvio (padrão Nacional ISSNet).

    1) Assina cada DPS (Reference=#Id do infDPS)
    2) Assina o LoteDps (Reference=#Id do lote) — exigido pelo Manual NotaControl
    """
    ns = "http://www.sped.fazenda.gov.br/nfse"
    root = etree.fromstring(xml_str.encode("utf-8"))
    root_local = etree.QName(root.tag).localname if root.tag else ""

    if root_local in ("DPS",):
        return assinar_xml_dps(xml_str, pfx_path, senha_pfx)

    key, cert_obj, extra_certs = _carregar_chave_xmlsec(pfx_path, senha_pfx)
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
        _assinar_elemento_por_id(dps, inf_dps, key, inf_id, cert_obj, extra_certs)

    # Signature do lote fica na raiz (irmã de LoteDps), Reference=#Id do LoteDps
    lote = root.find(f"{{{ns}}}LoteDps")
    if lote is not None and root_local in ("EnviarLoteDpsSincronoEnvio", "EnviarLoteDpsEnvio"):
        lote_id = (lote.get("Id") or "").strip()
        if not lote_id:
            num = lote.findtext(f"{{{ns}}}NumeroLote") or "1"
            lote_id = f"Lote{num}"
            lote.set("Id", lote_id)
        _assinar_elemento_por_id(root, lote, key, lote_id, cert_obj, extra_certs)

    result = etree.tostring(root, encoding="unicode", xml_declaration=False)
    logger.info(
        "XML lote DPS assinado (%s): %d DPS + assinatura do envio",
        root_local or "?",
        len(dps_nodes),
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
