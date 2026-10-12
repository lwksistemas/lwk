"""Processamento do webhook Asaas da conta do CRM (nota e comissão)."""
from __future__ import annotations

import logging
from typing import Any

from nfse_integration.asaas_webhook_loja import (
    invoice_payload_para_sync,
    processar_nota_webhook_asaas_loja,
)

logger = logging.getLogger(__name__)

__all__ = ["invoice_payload_para_sync", "process_asaas_loja_webhook_sync"]


def process_asaas_loja_webhook_sync(loja_id: int, payload: dict[str, Any]) -> None:
    """Sincroniza a nota e, se o pagamento for de comissão, dá baixa no relatório."""
    if not processar_nota_webhook_asaas_loja(loja_id, payload):
        return

    event = payload.get("event") or payload.get("type")
    payment = payload.get("payment") if isinstance(payload.get("payment"), dict) else {}
    try:
        if event in ("PAYMENT_RECEIVED", "PAYMENT_CONFIRMED") and payment.get("id"):
            from crm_vendas.models_relatorio_comissao import RelatorioComissao
            from crm_vendas.services_relatorio_comissao import processar_pagamento_comissao

            rc = RelatorioComissao.objects.filter(
                asaas_payment_id=payment["id"],
                status="aguardando_pagamento",
            ).first()
            if rc:
                logger.info("Pagamento confirmado para relatório comissão %s", rc.numero)
                processar_pagamento_comissao(rc)
    except Exception as rc_err:
        logger.warning("Falha ao processar pagamento de comissão: %s", rc_err, exc_info=True)
