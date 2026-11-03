"""Métricas agregadas de WhatsApp/Evolution — só contagens, sem PII."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def metricas_whatsapp_agregadas() -> dict[str, Any]:
    """Conta instâncias por status nas lojas ativas (schemas tenant)."""
    out: dict[str, Any] = {
        "wa_instancias": 0,
        "wa_conectadas": 0,
        "wa_desconectadas": 0,
        "wa_fonte": "tenant",
    }
    try:
        from core.db_config import ensure_loja_database_config
        from tenants.middleware import set_current_loja_id, set_current_tenant_db

        from clinica_beleza.catalogo_service import lojas_clinica_beleza_com_schema
    except Exception:
        try:
            from superadmin.models import Loja

            lojas = list(Loja.objects.filter(is_active=True).only("id", "database_name")[:200])
        except Exception:
            return out
    else:
        lojas = list(lojas_clinica_beleza_com_schema(apenas_ativas=True))

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
