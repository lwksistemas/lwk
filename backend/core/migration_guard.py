"""Verifica migrations críticas pendentes no banco default (evita 500 por schema desatualizado).
"""
from __future__ import annotations

import logging
import sys

logger = logging.getLogger(__name__)

# Apps cujo schema no default deve estar alinhado antes de servir tráfego
CRITICAL_APPS = ("superadmin", "auth", "contenttypes")


def _should_skip_check() -> bool:
    argv = sys.argv
    if not argv:
        return True
    script = argv[0]
    if "manage.py" in script or script.endswith("manage.py"):
        cmd = argv[1] if len(argv) > 1 else ""
        if cmd in (
            "migrate", "makemigrations", "showmigrations", "sqlmigrate",
            "test", "shell", "collectstatic", "check",
        ):
            return True
    return bool("pytest" in script or "py.test" in script)


def get_pending_critical_migrations(database: str = "default") -> list[tuple[str, str]]:
    from django.db import connections
    from django.db.migrations.executor import MigrationExecutor

    connection = connections[database]
    executor = MigrationExecutor(connection)
    targets = [
        key for key in executor.loader.graph.leaf_nodes()
        if key[0] in CRITICAL_APPS
    ]
    if not targets:
        return []
    plan = executor.migration_plan(targets)
    return [(migration.app_label, migration.name) for migration, _ in plan]


def run_migration_guard() -> None:
    """Loga ou impede boot se migrations críticas estiverem pendentes."""
    if _should_skip_check():
        return

    from django.conf import settings

    try:
        pending = get_pending_critical_migrations()
    except Exception as e:
        logger.warning("migration_guard: não foi possível verificar migrations: %s", e)
        return

    if not pending:
        return

    labels = [f"{app}.{name}" for app, name in pending]
    msg = (
        "Migrations críticas pendentes no banco default: "
        + ", ".join(labels)
        + ". Execute: python manage.py migrate"
    )
    strict = getattr(settings, "MIGRATION_GUARD_STRICT", not settings.DEBUG)
    if strict:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured(msg)
    logger.critical(msg)
