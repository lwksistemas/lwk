"""
Limpeza de instâncias Evolution (WhatsApp Web) — evita sessões órfãs lwk_loja_{id}.
"""
from __future__ import annotations

import logging
import re

from whatsapp.evolution_client import (
    delete_instance,
    evolution_configured,
    evolution_instance_name,
    fetch_instances,
)

logger = logging.getLogger(__name__)

INSTANCE_RE = re.compile(r'^lwk_loja_(\d+)(?:_\d+)?$', re.IGNORECASE)


def _instance_name_from_item(item: dict) -> str:
    if not isinstance(item, dict):
        return ''
    inst = item.get('instance') if isinstance(item.get('instance'), dict) else item
    return (inst.get('instanceName') or inst.get('name') or '').strip()


def delete_evolution_for_loja(loja_id: int, *, instance_name: str | None = None) -> dict:
    """
    Remove instância Evolution da loja (best-effort; 404 = ok).
    """
    if not evolution_configured():
        return {'skipped': True, 'reason': 'evolution_not_configured'}

    name = (instance_name or '').strip() or evolution_instance_name(loja_id)
    try:
        delete_instance(name)
        logger.info('Evolution: instância removida %s (loja_id=%s)', name, loja_id)
        return {'deleted': name, 'loja_id': loja_id, 'ok': True}
    except Exception as exc:
        logger.warning('Evolution: falha ao remover %s (loja_id=%s): %s', name, loja_id, exc)
        return {'deleted': name, 'loja_id': loja_id, 'ok': False, 'error': str(exc)}


def list_evolution_instances() -> list[dict]:
    """Lista instâncias com nome e loja_id parseado (quando lwk_loja_N)."""
    rows = []
    for item in fetch_instances():
        name = _instance_name_from_item(item)
        if not name:
            continue
        m = INSTANCE_RE.match(name)
        rows.append({
            'instance_name': name,
            'loja_id': int(m.group(1)) if m else None,
            'raw': item,
        })
    return rows


def find_orphan_evolution_instances(active_loja_ids: set[int] | None = None) -> list[dict]:
    """
    Instâncias lwk_loja_{id} cujo id não existe mais em superadmin_loja.
    """
    if active_loja_ids is None:
        from superadmin.models import Loja

        active_loja_ids = set(Loja.objects.values_list('id', flat=True))

    orphans = []
    for row in list_evolution_instances():
        lid = row.get('loja_id')
        if lid is None:
            continue
        if lid not in active_loja_ids:
            orphans.append(row)
    return orphans


def delete_orphan_evolution_instances(active_loja_ids: set[int] | None = None) -> list[dict]:
    results = []
    for row in find_orphan_evolution_instances(active_loja_ids):
        name = row['instance_name']
        lid = row['loja_id']
        try:
            delete_instance(name)
            results.append({'instance_name': name, 'loja_id': lid, 'ok': True})
            logger.info('Evolution órfã removida: %s (loja_id=%s inexistente)', name, lid)
        except Exception as exc:
            results.append({'instance_name': name, 'loja_id': lid, 'ok': False, 'error': str(exc)})
            logger.warning('Evolution órfã %s: %s', name, exc)
    return results
