"""Métricas agregadas de WhatsApp/Evolution — só contagens, sem PII."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _contagem_do_painel() -> dict[str, Any] | None:
    """Mesma lista do painel WhatsApp: Evolution, clínica e CRM."""
    from superadmin.services.whatsapp_painel_service import montar_painel

    painel = montar_painel()
    evolution = painel.get("evolution") or {}
    if not evolution.get("ok") and not evolution.get("parceiro_ok"):
        return None
    resumo = painel.get("resumo") or {}
    conectadas = int(resumo.get("conectados") or 0)
    aguardando = int(resumo.get("aguardando_qr") or 0)
    desconectadas = int(resumo.get("desconectados") or 0)
    return {
        "wa_instancias": conectadas + aguardando + desconectadas,
        "wa_conectadas": conectadas,
        "wa_desconectadas": desconectadas + aguardando,
        "wa_fonte": "evolution",
    }


def metricas_whatsapp_agregadas() -> dict[str, Any]:
    """Conta instâncias na Evolution (clínica e CRM), sem PII."""
    out: dict[str, Any] = {
        "wa_instancias": 0,
        "wa_conectadas": 0,
        "wa_desconectadas": 0,
        "wa_fonte": "tenant",
    }
    try:
        do_painel = _contagem_do_painel()
    except Exception:
        logger.debug("wa métricas: painel indisponível", exc_info=True)
        do_painel = None
    if do_painel is not None:
        return do_painel

    try:
        from superadmin.models import Loja

        lojas = list(
            Loja.objects.filter(is_active=True, database_created=True).only("id", "database_name")[:200]
        )
    except Exception:
        return out

    total = 0
    conectadas = 0
    for loja in lojas:
        db = getattr(loja, "database_name", None)
        if not db:
            continue
        try:
            from core.db_config import ensure_loja_database_config
            from tenants.middleware import set_current_loja_id, set_current_tenant_db

            if not ensure_loja_database_config(db, conn_max_age=0):
                continue
            set_current_loja_id(loja.id)
            set_current_tenant_db(db)
            from whatsapp.models import WhatsAppConfig

            for cfg in WhatsAppConfig.objects.all()[:5]:
                nome = (getattr(cfg, "evolution_instance_name", None) or "").strip()
                if not nome and not getattr(cfg, "whatsapp_connection_status", None):
                    continue
                total += 1
                st = (getattr(cfg, "whatsapp_connection_status", None) or "").lower()
                if st == "connected":
                    conectadas += 1
        except Exception:
            logger.debug("wa métricas loja %s ignorada", getattr(loja, "id", "?"), exc_info=True)
        finally:
            try:
                from tenants.middleware import set_current_loja_id, set_current_tenant_db

                set_current_loja_id(None)
                set_current_tenant_db("default")
            except Exception:
                pass

    out["wa_instancias"] = total
    out["wa_conectadas"] = conectadas
    out["wa_desconectadas"] = max(0, total - conectadas)
    return out
