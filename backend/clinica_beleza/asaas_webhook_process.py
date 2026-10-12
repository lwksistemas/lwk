"""Webhook Asaas da conta da clínica. Não abre comissão do CRM."""
from __future__ import annotations

from typing import Any

from nfse_integration.asaas_webhook_loja import processar_nota_webhook_asaas_loja


def process_asaas_clinica_webhook_sync(loja_id: int, payload: dict[str, Any]) -> None:
    processar_nota_webhook_asaas_loja(loja_id, payload)
