"""Cancela e reativa a assinatura sem apagar dados da loja."""
from django.utils import timezone

MOTIVO_ASSINATURA_CANCELADA = "Assinatura cancelada"


def assinatura_esta_cancelada(loja, financeiro=None) -> bool:
    if financeiro is None:
        financeiro = getattr(loja, "financeiro", None)
    if financeiro is None:
        return False
    return (
        financeiro.status_pagamento == "cancelado"
        and bool(getattr(loja, "is_blocked", False))
        and (getattr(loja, "blocked_reason", "") or "") == MOTIVO_ASSINATURA_CANCELADA
    )


def _marcar_cancelada(loja, financeiro):
    financeiro.status_pagamento = "cancelado"
    financeiro.save(update_fields=["status_pagamento"])
    loja.is_blocked = True
    loja.blocked_reason = MOTIVO_ASSINATURA_CANCELADA
    if not loja.blocked_at:
        loja.blocked_at = timezone.now()
    loja.save(update_fields=["is_blocked", "blocked_at", "blocked_reason", "updated_at"])


def cancelar_assinatura(loja, financeiro) -> dict:
    """Para boletos novos e bloqueia o acesso. Pagamentos, notas e cadastros ficam."""
    if assinatura_esta_cancelada(loja, financeiro):
        return {"success": False, "error": "A assinatura já está cancelada."}

    _marcar_cancelada(loja, financeiro)
    return {
        "success": True,
        "assinatura_cancelada": True,
        "message": (
            "Assinatura cancelada. O sistema para de emitir boletos e o acesso fica bloqueado. "
            "Nada do cliente foi apagado. Para voltar, use Reativar: o boleto é gerado e o acesso volta depois do pagamento."
        ),
    }


def reativar_assinatura(loja, financeiro, emitir=None) -> dict:
    """Gera o boleto da volta. O acesso só retorna quando esse pagamento for confirmado."""
    if not assinatura_esta_cancelada(loja, financeiro):
        return {"success": False, "error": "A assinatura não está cancelada."}

    from superadmin.financeiro_views.troca_banco import boleto_em_aberto

    if boleto_em_aberto(loja):
        return {
            "success": True,
            "boleto_emitido": False,
            "assinatura_cancelada": True,
            "message": (
                "Já existe boleto em aberto. O acesso volta quando esse boleto for pago. "
                "Nenhum outro boleto foi gerado."
            ),
        }

    if emitir is None:
        from superadmin.sync_service.asaas import AsaasSyncService

        emitir = AsaasSyncService().emitir_boleto
    resultado = emitir(loja) or {}
    financeiro.refresh_from_db()
    loja.refresh_from_db()
    _marcar_cancelada(loja, financeiro)
    if not resultado.get("success"):
        return {
            "success": False,
            "boleto_emitido": False,
            "assinatura_cancelada": True,
            "error": (
                "A assinatura segue cancelada e o boleto não foi emitido. "
                f"{resultado.get('error') or ''}"
            ).strip(),
        }
    aviso = resultado.get("message") or "Boleto de reativação emitido."
    return {
        "success": True,
        "boleto_emitido": True,
        "assinatura_cancelada": True,
        "boleto_url": resultado.get("boleto_url") or "",
        "message": f"{aviso} O acesso volta depois que o cliente pagar.",
    }
