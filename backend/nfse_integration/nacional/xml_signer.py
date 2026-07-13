"""
Assinatura digital XML (XMLDSIG) para NFS-e Nacional.

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


def carregar_certificado_pfx(pfx_path: str, senha: str) -> tuple:
    """
    Carrega chave privada e certificado de um arquivo .pfx/.p12.
    
    Returns:
        Tuple (private_key, certificate, extra_certs)
    """
    from cryptography.hazmat.primitives.serialization import pkcs12

    with open(pfx_path, 'rb') as f:
        pfx_data = f.read()

    private_key, certificate, extra = pkcs12.load_key_and_certificates(
        pfx_data, senha.encode()
    )
    if certificate is None:
        raise ValueError('O arquivo .pfx não contém certificado válido.')
    if private_key is None:
        raise ValueError('O arquivo .pfx não contém chave privada.')

    return private_key, certificate, extra


def carregar_certificado_bytes(pfx_bytes: bytes, senha: str) -> tuple:
    """
    Carrega certificado a partir de bytes (para uso com BinaryField do Django).
    """
    from cryptography.hazmat.primitives.serialization import pkcs12

    private_key, certificate, extra = pkcs12.load_key_and_certificates(
        pfx_bytes, senha.encode()
    )
    if certificate is None:
        raise ValueError('Os bytes do certificado não contêm certificado válido.')
    if private_key is None:
        raise ValueError('Os bytes do certificado não contêm chave privada.')

    return private_key, certificate, extra


def assinar_xml_dps(xml_str: str, pfx_path: str, senha_pfx: str) -> str:
    """
    Assina o XML da DPS com certificado digital.
    
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

    root = etree.fromstring(xml_str.encode('utf-8'))

    # Carregar chave privada e certificado
    private_key, cert_obj, _ = carregar_certificado_pfx(pfx_path, senha_pfx)

    from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat

    key_pem = private_key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())
    cert_pem = cert_obj.public_bytes(Encoding.PEM)

    # Criar chave xmlsec
    key = xmlsec.Key.from_memory(key_pem, xmlsec.constants.KeyDataFormatPem)
    key.load_cert_from_memory(cert_pem, xmlsec.constants.KeyDataFormatPem)

    # Encontrar o elemento infDPS e seu Id
    ns = 'http://www.sped.fazenda.gov.br/nfse'
    inf_dps = root.find(f'{{{ns}}}infDPS')
    if inf_dps is None:
        raise ValueError('Elemento infDPS não encontrado no XML')

    inf_id = inf_dps.get('Id')
    if not inf_id:
        raise ValueError('Atributo Id não encontrado em infDPS')

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
        uri=f'#{inf_id}',
    )
    xmlsec.template.add_transform(ref, xmlsec.constants.TransformEnveloped)
    xmlsec.template.add_transform(ref, xmlsec.constants.TransformInclC14N)

    # KeyInfo com X509Data
    key_info = xmlsec.template.ensure_key_info(sig_node)
    x509_data = xmlsec.template.add_x509_data(key_info)
    xmlsec.template.x509_data_add_certificate(x509_data)

    # Assinar
    ctx = xmlsec.SignatureContext()
    ctx.key = key
    ctx.register_id(inf_dps, 'Id', None)
    ctx.sign(sig_node)

    result = '<?xml version="1.0" encoding="UTF-8"?>' + etree.tostring(root, encoding='unicode', xml_declaration=False)
    logger.info('XML DPS assinado com sucesso (RSA-SHA1, Reference=#%s)', inf_id)
    return result


def assinar_xml_dps_bytes(xml_str: str, pfx_bytes: bytes, senha_pfx: str) -> str:
    """
    Assina XML da DPS usando certificado em bytes (BinaryField).
    Cria arquivo temporário e delega para assinar_xml_dps.
    """
    cert_path = None
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pfx')  # noqa: SIM115
        tmp.write(pfx_bytes)
        tmp.close()
        cert_path = tmp.name

        return assinar_xml_dps(xml_str, cert_path, senha_pfx)
    finally:
        if cert_path:
            with contextlib.suppress(OSError):
                os.unlink(cert_path)


def extrair_info_certificado(pfx_path: str, senha: str) -> dict:
    """
    Extrai informações do certificado para exibição.
    
    Returns:
        Dict com subject, issuer, valid_from, valid_to, cnpj
    """
    _, cert_obj, _ = carregar_certificado_pfx(pfx_path, senha)


    subject = cert_obj.subject.rfc4514_string()
    issuer = cert_obj.issuer.rfc4514_string()

    # Tentar extrair CNPJ do subject (OID 2.16.76.1.3.3)
    cnpj = ''
    try:
        for attr in cert_obj.subject:
            if attr.oid.dotted_string == '2.16.76.1.3.3':
                cnpj = attr.value
                break
    except Exception:
        pass

    return {
        'subject': subject[:500],
        'issuer': issuer[:500],
        'valid_from': cert_obj.not_valid_before_utc.isoformat(),
        'valid_to': cert_obj.not_valid_after_utc.isoformat(),
        'cnpj': cnpj,
    }
