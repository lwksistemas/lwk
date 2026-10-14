"""Troca o banco da assinatura sem reemitir boleto que já existe."""
from superadmin.models import PagamentoLoja

NOMES_BANCO = {
    "asaas": "Asaas",
    "mercadopago": "Mercado Pago",
    "cora": "Cora",
}


def nome_banco(codigo: str) -> str:
    return NOMES_BANCO.get((codigo or "").strip().lower(), "")


def boleto_em_aberto(loja):
    """Cobrança ainda não paga, em qualquer banco."""
    return (
        PagamentoLoja.objects.filter(loja=loja, status__in=["pendente", "atrasado"])
        .order_by("-data_vencimento", "-id")
        .first()
    )


def trocar_banco_assinatura(loja, provedor: str, emitir=None) -> dict:
    """Grava o banco da assinatura.

    Sem boleto em aberto, emite no banco novo. Com boleto já gerado, a troca
    vale só na próxima cobrança.
    """
    escolhido = (provedor or "").strip().lower()
    if escolhido not in NOMES_BANCO:
        return {"success": False, "error": "Escolha Asaas, Mercado Pago ou Cora."}

    atual = (getattr(loja, "provedor_boleto_preferido", None) or "asaas").strip().lower()
    if escolhido == atual:
        return {"success": False, "error": f"A assinatura já usa {NOMES_BANCO[escolhido]}."}

    aberto = boleto_em_aberto(loja)
    loja.provedor_boleto_preferido = escolhido
    loja.save(update_fields=["provedor_boleto_preferido", "updated_at"])

    if aberto:
        banco_deste_mes = nome_banco(aberto.provedor_boleto) or "banco atual"
        return {
            "success": True,
            "boleto_emitido": False,
            "provedor": escolhido,
            "provedor_display": NOMES_BANCO[escolhido],
            "message": (
                f"O boleto deste mês já foi gerado no {banco_deste_mes}. "
                f"A partir do próximo mês a cobrança sai pelo {NOMES_BANCO[escolhido]}."
            ),
        }

    if emitir is None:
        from superadmin.sync_service.asaas import AsaasSyncService

        emitir = AsaasSyncService().emitir_boleto
    resultado = emitir(loja) or {}
    if not resultado.get("success"):
        return {
            "success": False,
            "boleto_emitido": False,
            "provedor": escolhido,
            "provedor_display": NOMES_BANCO[escolhido],
            "error": (
                f"O banco da assinatura passou a ser {NOMES_BANCO[escolhido]}, "
                f"mas o boleto não foi emitido. {resultado.get('error') or ''}"
            ).strip(),
        }
    return {
        "success": True,
        "boleto_emitido": True,
        "provedor": escolhido,
        "provedor_display": NOMES_BANCO[escolhido],
        "boleto_url": resultado.get("boleto_url") or "",
        "message": resultado.get("message") or f"Banco alterado para {NOMES_BANCO[escolhido]} e o boleto foi emitido.",
    }
