"""Alinha django_migrations quando um filho está aplicado sem o pai.

O migrate do Django recusa qualquer app se o histórico de outro app estiver
inconsistente. No tenant da Clínica Geral isso aparece como:

    auth.0005_alter_user_last_login_null is applied before its dependency
    auth.0004_alter_user_username_opts

0004/0007/0011 são mudanças de validador/permissão, sem coluna nova. Marcar
como aplicadas (fake) é seguro quando as migrations seguintes já rodaram.
"""
from __future__ import annotations

import logging

from django.db.migrations.loader import MigrationLoader
from django.db.migrations.recorder import MigrationRecorder

logger = logging.getLogger(__name__)


def missing_ancestors(graph, applied: set[tuple[str, str]]) -> list[tuple[str, str]]:
    """Pais (e avós) de migrations já aplicadas que ainda não estão no recorder."""
    missing: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def walk(key: tuple[str, str]) -> None:
        node = graph.node_map.get(key)
        if node is None:
            return
        for parent in node.parents:
            parent_key = getattr(parent, "key", parent)
            if not isinstance(parent_key, tuple) or len(parent_key) != 2:
                continue
            if parent_key[0].startswith("__"):
                continue
            if parent_key in applied or parent_key in seen:
                continue
            seen.add(parent_key)
            missing.append(parent_key)
            walk(parent_key)

    for key in applied:
        walk(key)

    ordered: list[tuple[str, str]] = []
    already: set[tuple[str, str]] = set()
    for leaf in graph.leaf_nodes():
        try:
            plan = graph.forwards_plan(leaf)
        except Exception:
            continue
        for step in plan:
            if step in seen and step not in already:
                ordered.append(step)
                already.add(step)
    for step in missing:
        if step not in already:
            ordered.append(step)
    return ordered


def repair_inconsistent_history(connection) -> list[tuple[str, str]]:
    """Grava no recorder os pais ausentes. Retorna a lista marcada."""
    loader = MigrationLoader(connection, ignore_no_migrations=True)
    recorder = MigrationRecorder(connection)
    applied = set(recorder.applied_migrations())
    to_record = missing_ancestors(loader.graph, applied)
    recorded: list[tuple[str, str]] = []
    for app, name in to_record:
        if (app, name) in applied:
            continue
        recorder.record_applied(app, name)
        applied.add((app, name))
        recorded.append((app, name))
        logger.info("Migration fake (pai ausente): %s.%s", app, name)
    return recorded
