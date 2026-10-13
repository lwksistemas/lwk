"""Baixa da assinatura quando a Cora confirma o boleto pago."""

from __future__ import annotations

import logging

from django.utils import timezone

logger = logging.getLogger(__name__)


def cliente_da_config():
    from .cora_client import CoraClient
    from .models import CoraConfig

    config = CoraConfig.get_config()
    if not config.credencial_pronta:
        raise RuntimeError("Cora não configurada.")
    return CoraClient(config.client_id, config.certificado(), config.chave_privada()), config


def confirmar_fatura_paga(invoice_id: str) -> dict:
    """Consulta a fatura na Cora e, se estiver paga, renova a loja."""
    from .models import FinanceiroLoja, PagamentoLoja
    from .sync_service.mercadopago import _desbloquear_loja
    from .sync_service.nfse import tentar_emitir_nfse_assinatura

    invoice_id = (invoice_id or "").strip()
    if not invoice_id:
        return {"success": False, "processed": False}

    try:
        client, _config = cliente_da_config()
        fatura = client.consultar_fatura(invoice_id)
    except Exception:
        logger.exception("Falha ao consultar fatura Cora")
        return {"success": False, "processed": False}

    if fatura.get("status") != "PAID":
        return {"success": True, "processed": False, "status": fatura.get("status")}

    pagamento = PagamentoLoja.objects.filter(cora_invoice_id=invoice_id, provedor_boleto="cora").first()
    if pagamento is None:
        financeiro = FinanceiroLoja.objects.filter(cora_invoice_id=invoice_id, provedor_boleto="cora").select_related("loja").first()
        if financeiro is None:
            logger.warning("Fatura Cora %s sem loja vinculada", invoice_id)
            return {"success": True, "processed": False}
        pagamento = (
            PagamentoLoja.objects.filter(financeiro=financeiro, provedor_boleto="cora", status="pendente")
            .order_by("-data_vencimento")
            .first()
        )
        loja = financeiro.loja
    else:
        if pagamento.status == "pago":
            return {"success": True, "processed": False}
        loja = pagamento.loja
        financeiro = loja.financeiro

    if pagamento and pagamento.status != "pago":
        pagamento.status = "pago"
        pagamento.data_pagamento = timezone.now()
        pagamento.save(update_fields=["status", "data_pagamento"])

    from superadmin.services import FinanceiroService

    financeiro.status_pagamento = "ativo"
    financeiro.ultimo_pagamento = timezone.now()
    financeiro.data_proxima_cobranca = FinanceiroService.calcular_proxima_cobranca_apos_pagamento(
        financeiro, loja, timezone.now().date(),
    )
    financeiro.save()
    _atualizar_vencimento_assinatura(loja, financeiro.data_proxima_cobranca)
    _desbloquear_loja(loja)
    tentar_emitir_nfse_assinatura(pagamento, invoice_id)
    logger.info("Assinatura renovada pela Cora loja=%s fatura=%s", loja.slug, invoice_id)
    return {"success": True, "processed": True, "loja_slug": loja.slug}


def _atualizar_vencimento_assinatura(loja, proxima_data) -> None:
    try:
        from asaas_integration.models import LojaAssinatura
        assinatura = LojaAssinatura.objects.filter(loja_slug=loja.slug).first()
        if assinatura:
            assinatura.data_vencimento = proxima_data
            assinatura.save(update_fields=["data_vencimento"])
    except Exception:
        logger.warning("Não foi possível atualizar o vencimento da assinatura da loja %s", loja.slug)
