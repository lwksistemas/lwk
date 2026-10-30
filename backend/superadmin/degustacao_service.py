"""Demonstração da loja: usa o sistema sem boleto até a data combinada."""
from __future__ import annotations

import logging
from datetime import date, timedelta

from django.utils import timezone

logger = logging.getLogger(__name__)

MOTIVO_DEGUSTACAO_ENCERRADA = "Demonstração encerrada"
DIAS_DEGUSTACAO_MAX = 90


def em_degustacao(financeiro) -> bool:
    return str(getattr(financeiro, "status_pagamento", "") or "") == "degustacao"


def fim_degustacao(financeiro) -> date | None:
    return getattr(financeiro, "degustacao_ate", None)


def degustacao_acabou(financeiro, hoje: date | None = None) -> bool:
    if not em_degustacao(financeiro):
        return False
    ate = fim_degustacao(financeiro)
    if not ate:
        return False
    return (hoje or date.today()) > ate


def _avisar_fim(loja) -> None:
    owner = getattr(loja, "owner", None)
    email = (getattr(owner, "email", "") or "").strip()
    if not email:
        return
    from core.email_delivery import send_system_mail

    assunto = f"A demonstração de {loja.nome} acabou"
    texto = (
        f"A demonstração de {loja.nome} acabou.\n\n"
        "O sistema está bloqueado e nenhum boleto foi gerado.\n"
        "Entre na página de assinatura e escolha pagar o boleto ou cancelar a loja.\n"
        "Sem essa escolha, o acesso continua bloqueado."
    )
    send_system_mail(assunto, texto, [email], fail_silently=True)


def encerrar_degustacao_se_venceu(loja, financeiro, *, persistir: bool = True) -> dict | None:
    """No dia seguinte ao fim, bloqueia e avisa. Não gera boleto."""
    if not em_degustacao(financeiro):
        return None
    hoje = date.today()
    ate = fim_degustacao(financeiro)
    if ate and hoje <= ate:
        return {
            "loja_id": loja.id,
            "slug": getattr(loja, "slug", ""),
            "blocked": bool(getattr(loja, "is_blocked", False)),
            "status": "degustacao",
            "changed": False,
            "skipped": True,
            "reason": "degustacao_aberta",
        }

    changed = False
    if not loja.is_blocked or (getattr(loja, "blocked_reason", "") or "") != MOTIVO_DEGUSTACAO_ENCERRADA:
        loja.is_blocked = True
        loja.blocked_at = timezone.now()
        loja.blocked_reason = MOTIVO_DEGUSTACAO_ENCERRADA
        loja.days_overdue = 0
        changed = True
    if persistir and changed:
        loja.save(update_fields=["is_blocked", "blocked_at", "blocked_reason", "days_overdue", "updated_at"])
    if persistir and not getattr(financeiro, "degustacao_avisada", False):
        _avisar_fim(loja)
        financeiro.degustacao_avisada = True
        financeiro.save(update_fields=["degustacao_avisada"])
        changed = True
    return {
        "loja_id": loja.id,
        "slug": getattr(loja, "slug", ""),
        "blocked": True,
        "status": "degustacao",
        "changed": changed,
        "skipped": False,
        "reason": "degustacao_encerrada",
    }


def preparar_financeiro_degustacao(financeiro, dias: int):
    financeiro.status_pagamento = "degustacao"
    financeiro.degustacao_ate = date.today() + timedelta(days=dias)
    financeiro.data_proxima_cobranca = financeiro.degustacao_ate
    financeiro.degustacao_avisada = False
    financeiro.save(update_fields=[
        "status_pagamento",
        "degustacao_ate",
        "data_proxima_cobranca",
        "degustacao_avisada",
    ])
    return financeiro


def aceitar_boleto_degustacao(loja, financeiro) -> dict:
    """Gera o primeiro boleto. O acesso volta só depois do pagamento."""
    if not em_degustacao(financeiro) or not degustacao_acabou(financeiro):
        return {"success": False, "error": "A demonstração ainda está aberta."}

    from superadmin.cobranca_service import CobrancaService, cobranca_ja_registrada
    from superadmin.serializers.loja import _enviar_boleto_do_cadastro
    from superadmin.services.financeiro_service import FinanceiroService

    ate = financeiro.degustacao_ate
    financeiro.status_pagamento = "pendente"
    financeiro.data_proxima_cobranca = FinanceiroService.calcular_primeiro_vencimento(3)
    financeiro.save(update_fields=["status_pagamento", "data_proxima_cobranca"])
    if not cobranca_ja_registrada(financeiro):
        resultado = CobrancaService().criar_cobranca(loja, financeiro)
        if not resultado.get("success"):
            financeiro.status_pagamento = "degustacao"
            financeiro.data_proxima_cobranca = ate
            financeiro.save(update_fields=["status_pagamento", "data_proxima_cobranca"])
            return {"success": False, "error": resultado.get("error") or "Não foi possível gerar o boleto."}
    financeiro.refresh_from_db()
    _enviar_boleto_do_cadastro(loja, financeiro)
    return {
        "success": True,
        "boleto_url": financeiro.boleto_url or "",
        "message": "Boleto gerado. O acesso volta depois do pagamento.",
    }


def iniciar_contagem_degustacao(loja, financeiro, dias: int):
    """Abre a demonstração agora e libera o uso. Não gera boleto."""
    preparar_financeiro_degustacao(financeiro, dias)
    financeiro.degustacao_dias_apos_pagamento = None
    financeiro.save(update_fields=["degustacao_dias_apos_pagamento"])
    motivo_cancelada = "Assinatura cancelada"
    if getattr(loja, "is_blocked", False) and (getattr(loja, "blocked_reason", "") or "") != motivo_cancelada:
        loja.is_blocked = False
        loja.blocked_at = None
        loja.blocked_reason = ""
        loja.days_overdue = 0
        loja.save(update_fields=["is_blocked", "blocked_at", "blocked_reason", "days_overdue", "updated_at"])
        try:
            from superadmin.loja_utils import invalidate_loja_info_publica_cache
            invalidate_loja_info_publica_cache(loja)
        except Exception:
            logger.exception("Falha ao limpar o aviso de bloqueio da loja %s", getattr(loja, "slug", ""))
    if not getattr(financeiro, "senha_enviada", False):
        try:
            from superadmin.email_service import EmailService
            EmailService().enviar_senha_provisoria(loja, loja.owner)
        except Exception:
            logger.exception("Falha ao enviar senha da demonstração da loja %s", getattr(loja, "slug", ""))
    return financeiro


def tem_boleto_em_aberto(loja, financeiro) -> bool:
    from superadmin.financeiro_views.troca_banco import boleto_em_aberto

    if boleto_em_aberto(loja):
        return True
    if str(getattr(financeiro, "status_pagamento", "") or "") not in ("pendente", "atrasado"):
        return False
    return bool(
        getattr(financeiro, "boleto_url", None)
        or getattr(financeiro, "asaas_payment_id", None)
        or getattr(financeiro, "mercadopago_payment_id", None)
        or getattr(financeiro, "cora_invoice_id", None)
    )


def definir_degustacao_loja_existente(loja, financeiro, dias: int) -> dict:
    """Loja já criada: sem boleto, conta agora. Com boleto, conta depois do pagamento."""
    from superadmin.financeiro_views.assinatura_cancelamento import assinatura_esta_cancelada

    try:
        dias = int(dias)
    except (TypeError, ValueError):
        dias = 0
    if dias < 1 or dias > DIAS_DEGUSTACAO_MAX:
        return {"success": False, "error": "Escolha de 1 a 90 dias de demonstração."}
    if assinatura_esta_cancelada(loja, financeiro):
        return {"success": False, "error": "A assinatura está cancelada. Reative antes de abrir a demonstração."}

    if tem_boleto_em_aberto(loja, financeiro):
        financeiro.degustacao_dias_apos_pagamento = dias
        financeiro.save(update_fields=["degustacao_dias_apos_pagamento"])
        return {
            "success": True,
            "aguardando_pagamento": True,
            "em_degustacao": em_degustacao(financeiro),
            "degustacao_ate": financeiro.degustacao_ate.isoformat() if getattr(financeiro, "degustacao_ate", None) else None,
            "dias_apos_pagamento": dias,
            "message": (
                f"O boleto em aberto continua valendo. "
                f"A demonstração de {dias} dias começa quando ele for pago."
            ),
        }

    iniciar_contagem_degustacao(loja, financeiro, dias)
    ate = getattr(financeiro, "degustacao_ate", None)
    ate_txt = ate.strftime("%d/%m/%Y") if ate else "o prazo escolhido"
    return {
        "success": True,
        "aguardando_pagamento": False,
        "em_degustacao": True,
        "degustacao_ate": ate.isoformat() if ate else None,
        "dias_apos_pagamento": None,
        "message": (
            f"Demonstração de {dias} dias iniciada. "
            f"Nenhum boleto foi gerado. O acesso segue liberado até {ate_txt}."
        ),
    }


def cancelar_degustacao(loja, financeiro) -> dict:
    """Encerra sem boleto."""
    if not em_degustacao(financeiro):
        return {"success": False, "error": "Esta loja não está em demonstração."}
    from superadmin.financeiro_views.assinatura_cancelamento import cancelar_assinatura

    return cancelar_assinatura(loja, financeiro)
