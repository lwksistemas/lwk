"""Emissão automática de NFS-e para assinaturas."""
import logging

logger = logging.getLogger(__name__)


def emitir_nfse_assinatura_sync(pagamento, payment_id=""):
    """Emite NFS-e da assinatura (síncrono — worker ou cron)."""
    if not pagamento:
        logger.warning("PagamentoLoja não encontrado para emitir NFS-e: %s", payment_id)
        return
    try:
        from asaas_integration.models_nfse_config import SuperadminNFSeConfig

        nfse_config = SuperadminNFSeConfig.get_config()
        if nfse_config.provedor_nfse == "desabilitado":
            logger.info("NFS-e desabilitada — não emitindo para %s", payment_id)
            return
        if not nfse_config.emitir_automaticamente:
            logger.info("Emissão automática desativada — não emitindo para %s", payment_id)
            return
        from asaas_integration.nfse_assinatura_service import emitir_nfse_assinatura

        nf_result = emitir_nfse_assinatura(pagamento)
        if nf_result.get("success"):
            logger.info(
                "NFS-e emitida (%s) pagamento %s: %s",
                nfse_config.provedor_nfse,
                payment_id,
                nf_result.get("numero_nf"),
            )
        else:
            logger.warning(
                "Falha NFS-e (%s) pagamento %s: %s",
                nfse_config.provedor_nfse,
                payment_id,
                nf_result.get("error"),
            )
    except Exception as nf_err:
        logger.exception("Erro ao emitir NF assinatura %s: %s", payment_id, nf_err)


def tentar_emitir_nfse_assinatura(pagamento, payment_id=""):
    """Enfileira ou emite NFS-e da assinatura."""
    from nfse_integration.queue_dispatch import enqueue_emitir_nfse_assinatura, should_enqueue_nfse

    if should_enqueue_nfse() and pagamento:
        enqueue_emitir_nfse_assinatura(pagamento, payment_id)
        return
    emitir_nfse_assinatura_sync(pagamento, payment_id)
