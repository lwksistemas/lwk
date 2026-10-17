"""Número que a Evolution já disse que não tem WhatsApp.

O lembrete e a cobrança automática não tentam de novo esse telefone
até o cadastro do paciente ser alterado.
"""
from __future__ import annotations

import re

from django.utils import timezone


def ids_de_recusa_a_preservar(linhas) -> set:
    """Ids da última tentativa de cada telefone, quando ela foi 'sem WhatsApp'.

    A limpeza apaga o texto antigo, mas esta linha fica: sem ela o lembrete
    tentaria o mesmo número de novo no mês seguinte.
    ``linhas`` vem da mais nova para a mais antiga: (id, telefone, status, response).
    """
    vistos = set()
    manter = set()
    for log_id, telefone, status, response in linhas:
        digits = re.sub(r"\D", "", telefone or "")
        if len(digits) < 8:
            continue
        chave = digits[-8:]
        if chave in vistos:
            continue
        vistos.add(chave)
        if status == "falhou" and texto_diz_sem_whatsapp(response):
            manter.add(log_id)
    return manter


def texto_diz_sem_whatsapp(response) -> bool:
    if isinstance(response, dict):
        bruto = response.get("error") or response.get("message") or ""
    else:
        bruto = response or ""
    if not isinstance(bruto, str):
        bruto = str(bruto)
    low = bruto.lower()
    return "não encontrado no whatsapp" in low or "nao encontrado no whatsapp" in low


def recusa_sem_whatsapp(loja_id, telefone, *, db=None):
    """Data da última tentativa, se ela foi 'número sem WhatsApp'. Senão None."""
    from whatsapp.models import WhatsAppLog

    digits = re.sub(r"\D", "", telefone or "")
    if loja_id is None or len(digits) < 8:
        return None
    qs = WhatsAppLog.objects.using(db) if db else WhatsAppLog.objects
    try:
        ultimo = (
            qs.filter(loja_id=loja_id, telefone__icontains=digits[-8:])
            .order_by("-created_at")
            .values_list("status", "response", "created_at")
            .first()
        )
    except Exception:
        return None
    if not ultimo:
        return None
    status, response, created_at = ultimo
    if status != "falhou" or not texto_diz_sem_whatsapp(response):
        return None
    return created_at


def pular_numero_recusado(patient, loja_id, *, db=None) -> bool:
    """True quando o automático deve pular este paciente."""
    telefone = (
        getattr(patient, "phone", None)
        or getattr(patient, "telefone", None)
        or ""
    )
    recusa = recusa_sem_whatsapp(loja_id, telefone, db=db)
    if recusa is None:
        return False
    atualizado = getattr(patient, "updated_at", None)
    if atualizado is None:
        return True
    if timezone.is_naive(recusa):
        recusa = timezone.make_aware(recusa, timezone.get_current_timezone())
    if timezone.is_naive(atualizado):
        atualizado = timezone.make_aware(atualizado, timezone.get_current_timezone())
    return atualizado <= recusa
