"""Disparo imediato de lembretes ao salvar atividade (complementa o cron)."""
from __future__ import annotations

import logging
from datetime import timedelta

from django.utils import timezone

logger = logging.getLogger(__name__)


def _marcar_enviado(atividade, campo: str) -> None:
    from crm_vendas.models import Atividade
    from tenants.middleware import get_current_tenant_db

    db_name = get_current_tenant_db()
    if db_name and db_name != "default":
        Atividade.objects.using(db_name).filter(pk=atividade.pk).update(
            **{campo: timezone.now()},
        )
    else:
        Atividade.objects.filter(pk=atividade.pk).update(**{campo: timezone.now()})


def tentar_lembretes_imediatos(loja_id: int, atividade) -> int:
    """Envia lembrete se a atividade está na janela 24h/2h ou foi agendada em cima da hora.
    """
    from crm_vendas.atividade_lembrete_tasks import _janela_antecedencia
    from crm_vendas.atividade_whatsapp_service import enviar_lembrete_atividade_whatsapp

    if not getattr(atividade, "lembrete_whatsapp", False):
        return 0
    if not (getattr(atividade, "lembrete_whatsapp_telefone", "") or "").strip():
        return 0
    if getattr(atividade, "concluido", False) or not atividade.data:
        return 0

    agora = timezone.now()
    if atividade.data <= agora:
        return 0

    delta = atividade.data - agora
    enviados = 0

    try:
        inicio_2h, fim_2h, campo_2h, _ = _janela_antecedencia("2h")
        enviar_2h = (
            not getattr(atividade, "lembrete_2h_enviado_em", None)
            and (
                inicio_2h <= atividade.data <= fim_2h
                or delta <= timedelta(hours=2, minutes=20)
            )
        )
        if enviar_2h:
            ok, err = enviar_lembrete_atividade_whatsapp(loja_id, atividade, "2h")
            if ok:
                _marcar_enviado(atividade, campo_2h)
                enviados += 1
                logger.info("Lembrete 2h imediato atividade %s loja %s", atividade.pk, loja_id)
            elif err:
                logger.warning("Lembrete 2h imediato falhou atividade %s: %s", atividade.pk, err)
            return enviados

        inicio_24h, fim_24h, campo_24h, _ = _janela_antecedencia("24h")
        if (
            not getattr(atividade, "lembrete_24h_enviado_em", None)
            and inicio_24h <= atividade.data <= fim_24h
        ):
            ok, err = enviar_lembrete_atividade_whatsapp(loja_id, atividade, "24h")
            if ok:
                _marcar_enviado(atividade, campo_24h)
                enviados += 1
                logger.info("Lembrete 24h imediato atividade %s loja %s", atividade.pk, loja_id)
            elif err:
                logger.warning("Lembrete 24h imediato falhou atividade %s: %s", atividade.pk, err)
    except Exception:
        logger.exception("Erro lembrete imediato atividade %s", getattr(atividade, "pk", "?"))

    return enviados
