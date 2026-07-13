"""Assinatura XML ABRASF 2.04 para ISSNet (RSA-SHA1, dupla assinatura em lote RPS)."""
import logging

from lxml import etree

from nfse_integration.issnet_cert import carregar_certificado
from nfse_integration.issnet_constants import NS_NFSE

logger = logging.getLogger(__name__)


def assinar_xml_issnet(xml_str: str, certificado_path: str, senha_certificado: str) -> str:
    """Assina XML com certificado digital A1 usando python-xmlsec.

    Dupla assinatura alinhada ao sped-nfse-issnet (PHP): primeiro o ``Rps`` externo
    (ListaRps/Rps) com Reference URI vazia e transform enveloped; depois a raiz
    ``EnviarLoteRpsEnvio`` também com URI vazia.
    """
    import xmlsec
    from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat

    root = etree.fromstring(xml_str.encode("utf-8"))

    private_key_obj, cert_obj, _ = carregar_certificado(certificado_path, senha_certificado)
    key_pem = private_key_obj.private_bytes(
        Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption(),
    )
    cert_pem = cert_obj.public_bytes(Encoding.PEM)

    key = xmlsec.Key.from_memory(key_pem, xmlsec.constants.KeyDataFormatPem)
    key.load_cert_from_memory(cert_pem, xmlsec.constants.KeyDataFormatPem)

    def _append_x509_template(sig_node):
        key_info = xmlsec.template.ensure_key_info(sig_node)
        x509_data = xmlsec.template.add_x509_data(key_info)
        xmlsec.template.x509_data_add_certificate(x509_data)

    def _template_sig_enveloped_only(parent_el, ref_uri):
        sig_node = xmlsec.template.create(
            parent_el,
            xmlsec.constants.TransformInclC14N,
            xmlsec.constants.TransformRsaSha1,
        )
        parent_el.append(sig_node)
        ref = xmlsec.template.add_reference(
            sig_node,
            xmlsec.constants.TransformSha1,
            uri=ref_uri,
        )
        xmlsec.template.add_transform(ref, xmlsec.constants.TransformEnveloped)
        _append_x509_template(sig_node)
        return sig_node

    ns = NS_NFSE
    root_local = etree.QName(root.tag).localname if root.tag else ""

    def _sign_cancelamento_por_pedido(root_el):
        pedido = root_el.find(f"{{{ns}}}Pedido")
        if pedido is None:
            return None
        pedido_id = (pedido.get("Id") or "").strip() or "Pedido1"
        pedido.set("Id", pedido_id)
        sig_ped = _template_sig_enveloped_only(pedido, f"#{pedido_id}")
        ctx_c = xmlsec.SignatureContext()
        ctx_c.key = key
        ctx_c.register_id(pedido, "Id", None)
        ctx_c.sign(sig_ped)
        return pedido_id

    def _sign_cancelamento_por_inf_pedido(root_el):
        pedido = root_el.find(f"{{{ns}}}Pedido")
        if pedido is None:
            return None
        inf = pedido.find(f"{{{ns}}}InfPedidoCancelamento")
        if inf is None:
            return None
        inf_id = (inf.get("Id") or "").strip() or "s01"
        inf.set("Id", inf_id)
        sig_inf = _template_sig_enveloped_only(pedido, f"#{inf_id}")
        ctx_c = xmlsec.SignatureContext()
        ctx_c.key = key
        ctx_c.register_id(inf, "Id", None)
        ctx_c.sign(sig_inf)
        return inf_id

    if root_local == "CancelarNfseEnvio":
        pedido = root.find(f"{{{ns}}}Pedido")
        inf = pedido.find(f"{{{ns}}}InfPedidoCancelamento") if pedido is not None else None
        inf_id = (inf.get("Id") or "").strip() if inf is not None else ""
        if inf_id.lower().startswith("cancel"):
            _sign_cancelamento_por_inf_pedido(root)
            result = etree.tostring(root, encoding="unicode")
            logger.info("XML assinado com xmlsec (cancelamento InfPedidoCancelamento)")
            logger.info("XML CANCELAMENTO ASSINADO COMPLETO: %s", result)
            return result

        pedido_id = _sign_cancelamento_por_pedido(root)
        if not pedido_id:
            _sign_cancelamento_por_inf_pedido(root)
        result = etree.tostring(root, encoding="unicode")
        logger.info("XML assinado com xmlsec (cancelamento Pedido)")
        logger.info("XML CANCELAMENTO ASSINADO COMPLETO: %s", result)
        return result

    if root_local == "ConsultarUrlNfseEnvio":
        sig_consulta = _template_sig_enveloped_only(root, "")
        ctx_c = xmlsec.SignatureContext()
        ctx_c.key = key
        ctx_c.sign(sig_consulta)
        result = etree.tostring(root, encoding="unicode")
        logger.info("XML assinado com xmlsec (ConsultarUrlNfse)")
        return result

    if root_local in (
        "ConsultarNfseServicoPrestadoEnvio",
        "ConsultarNfsePorFaixaEnvio",
    ):
        sig_consulta = _template_sig_enveloped_only(root, "")
        ctx_c = xmlsec.SignatureContext()
        ctx_c.key = key
        ctx_c.sign(sig_consulta)
        result = etree.tostring(root, encoding="unicode")
        logger.info("XML assinado com xmlsec (%s)", root_local)
        return result

    if root_local == "ConsultarNfseRpsEnvio":
        sig_consulta = _template_sig_enveloped_only(root, "")
        ctx_c = xmlsec.SignatureContext()
        ctx_c.key = key
        ctx_c.sign(sig_consulta)
        result = etree.tostring(root, encoding="unicode")
        logger.info("XML assinado com xmlsec (ConsultarNfseRps)")
        return result

    lista = root.find(f".//{{{ns}}}ListaRps")
    outer_rps = lista.find(f"{{{ns}}}Rps") if lista is not None else None

    if outer_rps is None:
        logger.warning("Assinatura: ListaRps/Rps externo nao encontrado; XML nao assinado.")
    else:
        sig_rps = _template_sig_enveloped_only(outer_rps, "")
        ctx = xmlsec.SignatureContext()
        ctx.key = key
        ctx.sign(sig_rps)

    if root_local not in ("EnviarLoteRpsEnvio", "EnviarLoteRpsSincronoEnvio"):
        logger.warning("Assinatura: raiz inesperada %s; pulando segunda assinatura.", root_local)
    else:
        sig_envio = _template_sig_enveloped_only(root, "")
        ctx2 = xmlsec.SignatureContext()
        ctx2.key = key
        ctx2.sign(sig_envio)

    result = etree.tostring(root, encoding="unicode")
    logger.info("XML assinado com xmlsec (RSA-SHA1, dupla assinatura ISSNET)")
    return result
