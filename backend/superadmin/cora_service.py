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


def receber_na_conta_empresa(invoice_id: str, forma: str) -> dict:
    """PIX ou transferência caiu na conta da empresa: baixa a fatura Cora e renova a loja."""
    from .models import PagamentoLoja

    invoice_id = (invoice_id or "").strip()
    if not invoice_id:
        return {"success": False, "error": "Não há boleto Cora em aberto para esta loja."}

    pagamento = (
        PagamentoLoja.objects.filter(cora_invoice_id=invoice_id, provedor_boleto="cora")
        .select_related("loja")
        .first()
    )
    if pagamento is None:
        return {"success": False, "error": "Não há boleto Cora em aberto para esta loja."}
    if pagamento.status == "pago":
        return {"success": False, "error": "Este boleto Cora já está pago."}

    try:
        client, _config = cliente_da_config()
        fatura = client.consultar_fatura(invoice_id)
    except Exception:
        logger.exception("Falha ao consultar fatura Cora %s", invoice_id)
        return {"success": False, "error": "Não foi possível consultar o boleto na Cora."}

    status_cora = (fatura.get("status") or "").upper()
    if status_cora == "PAID":
        resultado = confirmar_fatura_paga(invoice_id)
    elif status_cora == "CANCELLED":
        return {"success": False, "error": "O boleto Cora já foi cancelado."}
    else:
        try:
            client.cancelar_fatura(invoice_id)
        except Exception:
            logger.exception("Falha ao cancelar fatura Cora %s", invoice_id)
            return {"success": False, "error": "Não foi possível dar baixa no boleto Cora."}
        resultado = _renovar_apos_baixa_manual(pagamento, invoice_id)

    if not resultado.get("processed") and not resultado.get("success"):
        return {"success": False, "error": "Não foi possível atualizar a assinatura."}
    if resultado.get("success") is False:
        return resultado
    pagamento.refresh_from_db()
    if pagamento.status != "pago":
        return {"success": False, "error": "Não foi possível atualizar a assinatura."}
    pagamento.forma_pagamento = forma
    pagamento.save(update_fields=["forma_pagamento"])
    return {"success": True, "processed": True, "payment_id": invoice_id}


def _renovar_apos_baixa_manual(pagamento, invoice_id: str) -> dict:
    """Renova a loja depois que a fatura Cora em aberto foi cancelada por recebimento fora do boleto."""
    from .models import FinanceiroLoja
    from .sync_service.mercadopago import _desbloquear_loja
    from .sync_service.nfse import tentar_emitir_nfse_assinatura

    loja = pagamento.loja
    try:
        financeiro = loja.financeiro
    except FinanceiroLoja.DoesNotExist:
        return {"success": False, "processed": False}

    if pagamento.status != "pago":
        pagamento.status = "pago"
        pagamento.data_pagamento = timezone.now()
        pagamento.save(update_fields=["status", "data_pagamento"])

    from superadmin.services import FinanceiroService

    financeiro.status_pagamento = "ativo"
    financeiro.ultimo_pagamento = timezone.now()
    financeiro.data_proxima_cobranca = FinanceiroService.calcular_proxima_cobranca_apos_pagamento(
        financeiro, loja, timezone.now().date(),
    )
    financeiro.cora_invoice_id = ""
    financeiro.boleto_url = ""
    financeiro.save()
    _atualizar_vencimento_assinatura(loja, financeiro.data_proxima_cobranca)
    _desbloquear_loja(loja)
    tentar_emitir_nfse_assinatura(pagamento, invoice_id)
    logger.info("Assinatura renovada por recebimento na conta loja=%s fatura=%s", loja.slug, invoice_id)
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
