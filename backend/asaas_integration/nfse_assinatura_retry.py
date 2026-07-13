"""Reemite NFS-e de assinatura para pagamentos confirmados sem nota emitida."""
import logging

from django.db.models import Exists, OuterRef

logger = logging.getLogger(__name__)


def processar_nfse_assinatura_pendentes(limit: int = 15) -> int:
    """Tenta emitir NFS-e para pagamentos pagos que ainda não têm nota.
    Rede de segurança quando a emissão falhou no webhook (ex.: CEP inválido).
    """
    from asaas_integration.models_nfse_config import SuperadminNFSeConfig
    from superadmin.models import NFSeEmitida, PagamentoLoja
    from superadmin.sync_service import tentar_emitir_nfse_assinatura

    config = SuperadminNFSeConfig.get_config()
    if config.provedor_nfse == "desabilitado" or not config.emitir_automaticamente:
        return 0

    emitidas = NFSeEmitida.objects.filter(pagamento_id=OuterRef("pk"), status="emitida")
    pendentes = (
        PagamentoLoja.objects.filter(status="pago")
        .annotate(ja_emitida=Exists(emitidas))
        .filter(ja_emitida=False)
        .select_related("loja", "loja__owner")
        .order_by("-data_pagamento", "-id")[:limit]
    )

    emitidos = 0
    for pagamento in pendentes:
        antes = NFSeEmitida.objects.filter(pagamento=pagamento, status="emitida").exists()
        tentar_emitir_nfse_assinatura(pagamento, pagamento.asaas_payment_id or "")
        if NFSeEmitida.objects.filter(pagamento=pagamento, status="emitida").exists() and not antes:
            emitidos += 1
            logger.info(
                "NFS-e pendente emitida: loja=%s pagamento=%s",
                pagamento.loja.slug,
                pagamento.id,
            )

    if emitidos:
        logger.info("processar_nfse_assinatura_pendentes: %s nota(s) emitida(s)", emitidos)
    return emitidos
