"""Limpeza de instâncias Evolution (WhatsApp Web) — evita sessões órfãs e fantasmas.

Padrão de nome: lwk_loja_{id} ou lwk_loja_{id}_{suffix} (após rotação).
"""
from __future__ import annotations

import logging
import re

from whatsapp.evolution_client import (
    delete_instance,
    evolution_configured,
    evolution_instance_name,
    fetch_instances,
    logout_instance,
)

logger = logging.getLogger(__name__)

INSTANCE_RE = re.compile(r"^lwk_loja_(\d+)(?:_\d+)?$", re.IGNORECASE)


def _instance_name_from_item(item: dict) -> str:
    if not isinstance(item, dict):
        return ""
    inst = item.get("instance") if isinstance(item.get("instance"), dict) else item
    return (inst.get("instanceName") or inst.get("name") or "").strip()


def loja_id_from_instance_name(instance_name: str) -> int | None:
    m = INSTANCE_RE.match((instance_name or "").strip())
    return int(m.group(1)) if m else None


def list_evolution_instances() -> list[dict]:
    """Lista instâncias com nome e loja_id parseado (quando lwk_loja_N)."""
    rows = []
    for item in fetch_instances():
        name = _instance_name_from_item(item)
        if not name:
            continue
        m = INSTANCE_RE.match(name)
        rows.append({
            "instance_name": name,
            "loja_id": int(m.group(1)) if m else None,
            "raw": item,
        })
    return rows


def find_instances_for_loja(loja_id: int) -> list[dict]:
    """Todas as instâncias Evolution vinculadas a uma loja (inclui sufixos rotacionados)."""
    lid = int(loja_id)
    return [row for row in list_evolution_instances() if row.get("loja_id") == lid]


def _best_effort_remove_instance(instance_name: str, loja_id: int | None = None) -> dict:
    name = (instance_name or "").strip()
    if not name:
        return {"instance_name": name, "loja_id": loja_id, "ok": False, "error": "empty_name"}
    try:
        logout_instance(name)
    except Exception as exc:
        logger.debug("Evolution logout %s: %s", name, exc)
    try:
        delete_instance(name)
        logger.info("Evolution: instância removida %s (loja_id=%s)", name, loja_id)
        return {"instance_name": name, "loja_id": loja_id, "ok": True}
    except Exception as exc:
        logger.warning("Evolution: falha ao remover %s (loja_id=%s): %s", name, loja_id, exc)
        return {"instance_name": name, "loja_id": loja_id, "ok": False, "error": str(exc)}


def delete_all_evolution_instances_for_loja(
    loja_id: int,
    *,
    keep: str | None = None,
) -> list[dict]:
    """Remove todas as instâncias Evolution de uma loja, exceto `keep` (se informado).
    """
    if not evolution_configured():
        return [{"loja_id": loja_id, "ok": False, "skipped": True, "reason": "evolution_not_configured"}]

    keep_name = (keep or "").strip()
    results = []
    for row in find_instances_for_loja(loja_id):
        name = row["instance_name"]
        if keep_name and name == keep_name:
            continue
        results.append(_best_effort_remove_instance(name, loja_id))
    return results


def delete_evolution_for_loja(loja_id: int, *, instance_name: str | None = None) -> dict:
    """Remove instância(s) Evolution da loja.
    Sem instance_name: remove TODAS (evita fantasmas após rotação).
    Com instance_name: remove só essa (legado).
    """
    if not evolution_configured():
        return {"skipped": True, "reason": "evolution_not_configured"}

    if instance_name:
        return _best_effort_remove_instance(instance_name, loja_id)

    results = delete_all_evolution_instances_for_loja(loja_id)
    ok = sum(1 for r in results if r.get("ok"))
    return {
        "loja_id": loja_id,
        "ok": ok > 0 or not results,
        "removed": ok,
        "total": len(results),
        "details": results,
    }


def get_active_evolution_instance_by_loja() -> dict[int, str]:
    """Nome de instância ativo por loja (WhatsAppConfig no schema tenant).
    """
    from core.db_config import ensure_loja_database_config
    from superadmin.models import Loja
    from whatsapp.models import WhatsAppConfig

    active: dict[int, str] = {}
    for loja in Loja.objects.using("default").only("id", "database_name"):
        db = loja.database_name
        if not db:
            continue
        try:
            ensure_loja_database_config(db, conn_max_age=0)
            cfg = WhatsAppConfig.objects.using(db).filter(loja_id=loja.id).first()
        except Exception as exc:
            logger.debug("Evolution active instance loja %s: %s", loja.id, exc)
            continue
        if not cfg:
            continue
        if getattr(cfg, "whatsapp_provider", "") != WhatsAppConfig.PROVIDER_EVOLUTION:
            continue
        name = (getattr(cfg, "evolution_instance_name", None) or "").strip()
        active[loja.id] = name or evolution_instance_name(loja.id)
    return active


def find_orphan_evolution_instances(active_loja_ids: set[int] | None = None) -> list[dict]:
    """Instâncias lwk_loja_{id} cujo id não existe em superadmin_loja **deste ambiente**.

    Em Evolution compartilhada (staging + prod no mesmo servidor), muitas entradas
    são de outro ambiente — use find_cross_environment_evolution_instances().
    """
    return find_cross_environment_evolution_instances(active_loja_ids)


def find_cross_environment_evolution_instances(active_loja_ids: set[int] | None = None) -> list[dict]:
    """Instâncias válidas lwk_loja_{id} sem loja correspondente no banco local."""
    if active_loja_ids is None:
        from superadmin.models import Loja

        active_loja_ids = set(Loja.objects.values_list("id", flat=True))

    cross = []
    for row in list_evolution_instances():
        lid = row.get("loja_id")
        if lid is None:
            continue
        if lid not in active_loja_ids:
            cross.append(row)
    return cross


def evolution_shared_with_other_environment(active_loja_ids: set[int] | None = None) -> bool:
    """True quando há instâncias de lojas que existem só em outro ambiente LWK
    (Evolution API compartilhada entre staging e produção).
    """
    from django.conf import settings

    if getattr(settings, "EVOLUTION_DEDICATED", False):
        return False
    return bool(find_cross_environment_evolution_instances(active_loja_ids))


def classify_evolution_instances(active_loja_ids: set[int] | None = None) -> dict:
    """Agrupa instâncias para auditoria e limpeza segura."""
    if active_loja_ids is None:
        from superadmin.models import Loja

        active_loja_ids = set(Loja.objects.values_list("id", flat=True))

    active_by_loja = get_active_evolution_instance_by_loja()
    local = []
    cross = []
    non_standard = []
    for row in list_evolution_instances():
        lid = row.get("loja_id")
        row["instance_name"]
        if lid is None:
            non_standard.append(row)
        elif lid not in active_loja_ids:
            cross.append(row)
        else:
            local.append({**row, "active_instance": active_by_loja.get(lid)})
    stale = find_stale_evolution_instances(active_by_loja)
    return {
        "local": local,
        "cross_environment": cross,
        "non_standard": non_standard,
        "stale": stale,
        "shared_evolution": evolution_shared_with_other_environment(active_loja_ids),
    }


def find_stale_evolution_instances(
    active_by_loja: dict[int, str] | None = None,
) -> list[dict]:
    """Instâncias de lojas ativas que não são a instância registrada no WhatsAppConfig
    (duplicatas / sessões fantasmas após rotação).
    """
    if active_by_loja is None:
        active_by_loja = get_active_evolution_instance_by_loja()

    active_loja_ids = set(active_by_loja.keys())
    stale = []
    for row in list_evolution_instances():
        lid = row.get("loja_id")
        if lid is None or lid not in active_loja_ids:
            continue
        name = row["instance_name"]
        if name != active_by_loja.get(lid):
            stale.append({**row, "active_instance": active_by_loja.get(lid)})
    return stale


def cleanup_stale_and_orphan_evolution_instances(
    *,
    active_loja_ids: set[int] | None = None,
    allow_cross_environment: bool = False,
) -> dict:
    """Remove duplicatas (stale) e, opcionalmente, instâncias sem loja local.

    Com Evolution compartilhada entre ambientes, NÃO remove cross-environment
    sem allow_cross_environment=True (evita apagar WhatsApp de produção no staging).
    """
    if not evolution_configured():
        return {"skipped": True, "reason": "evolution_not_configured"}

    if active_loja_ids is None:
        from superadmin.models import Loja

        active_loja_ids = set(Loja.objects.values_list("id", flat=True))

    results: list[dict] = []
    shared = evolution_shared_with_other_environment(active_loja_ids)
    cross = find_cross_environment_evolution_instances(active_loja_ids)

    if cross and not allow_cross_environment:
        if shared:
            logger.warning(
                "Evolution compartilhada: %s instância(s) cross-env ignoradas na limpeza",
                len(cross),
            )
        else:
            for row in cross:
                results.append(_best_effort_remove_instance(row["instance_name"], row.get("loja_id")))
    elif cross and allow_cross_environment:
        for row in cross:
            results.append(_best_effort_remove_instance(row["instance_name"], row.get("loja_id")))

    active_by_loja = get_active_evolution_instance_by_loja()
    for row in find_stale_evolution_instances(active_by_loja):
        results.append(_best_effort_remove_instance(row["instance_name"], row.get("loja_id")))

    ok = sum(1 for r in results if r.get("ok"))
    return {
        "removed": ok,
        "failed": len(results) - ok,
        "total": len(results),
        "shared_evolution": shared,
        "cross_environment_skipped": len(cross) if shared and not allow_cross_environment else 0,
        "details": results,
    }


def delete_orphan_evolution_instances(
    active_loja_ids: set[int] | None = None,
    *,
    allow_cross_environment: bool = False,
) -> list[dict]:
    if evolution_shared_with_other_environment(active_loja_ids) and not allow_cross_environment:
        return []
    results = []
    for row in find_cross_environment_evolution_instances(active_loja_ids):
        results.append(_best_effort_remove_instance(row["instance_name"], row.get("loja_id")))
    return results
