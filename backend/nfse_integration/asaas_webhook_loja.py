"""Atualiza a nota da loja a partir do webhook Asaas.

Não lê comissão do CRM. Cada app chama esta função e trata o próprio pagamento.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def invoice_payload_para_sync(payload: dict) -> tuple[str, dict]:
    """Retorna (event, invoice_dict) para sincronizar a nota.
    O Asaas envia `invoice` no corpo; em alguns eventos pode vir só em `payment`.
    """
    event = payload.get("event") or payload.get("type") or ""
    invoice = payload.get("invoice") if isinstance(payload.get("invoice"), dict) else {}
    if not invoice.get("id") and isinstance(payload.get("payment"), dict):
        pay = payload["payment"]
        inv = pay.get("invoice") if isinstance(pay.get("invoice"), dict) else {}
        if inv.get("id"):
            invoice = inv
        elif pay.get("invoiceId"):
            invoice = {"id": pay.get("invoiceId"), "status": pay.get("invoiceStatus")}
    return event, invoice


def processar_nota_webhook_asaas_loja(loja_id: int, payload: dict[str, Any]) -> bool:
    """Abre o schema da loja e atualiza a NFS-e. Devolve False se a loja não abrir."""
    from django.conf import settings

    from core.db_config import ensure_loja_database_config
    from superadmin.models import Loja
    from tenants.middleware import set_current_loja_id, set_current_tenant_db

    loja = Loja.objects.using("default").filter(id=loja_id).first()
    if not loja:
        logger.warning("Webhook Asaas loja: loja_id=%s não encontrada", loja_id)
        return False

    db_name = getattr(loja, "database_name", None) or f'loja_{getattr(loja, "slug", loja.id)}'.replace("-", "_")
    if not ensure_loja_database_config(db_name, conn_max_age=0) or db_name not in settings.DATABASES:
        logger.warning("Webhook Asaas loja: schema %s indisponível", db_name)
        return False

    set_current_loja_id(loja_id)
    set_current_tenant_db(db_name)

    event = payload.get("event") or payload.get("type")
    payment = payload.get("payment") if isinstance(payload.get("payment"), dict) else {}
    invoice = payload.get("invoice") if isinstance(payload.get("invoice"), dict) else {}
    logger.info(
        "Asaas webhook nota id=%s slug=%s event=%s payment_id=%s invoice_id=%s",
        loja.id,
        loja.slug,
        event,
        payment.get("id"),
        invoice.get("id"),
    )

    try:
        ev, inv = invoice_payload_para_sync(payload)
        if inv.get("id"):
            from nfse_integration.asaas_webhook_sync import sincronizar_nfse_com_webhook_invoice

            sincronizar_nfse_com_webhook_invoice(ev, inv)
    except Exception as sync_err:
        logger.warning("Falha ao sincronizar NFS-e com webhook Asaas: %s", sync_err, exc_info=True)
    return True
