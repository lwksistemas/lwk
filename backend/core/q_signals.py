"""Fecha conexões de schema de loja após cada tarefa django-q.

O worker não passa pelo TenantMiddleware; sem isso o alias loja_* fica aberto
até o processo reciclar (recycle=500) e soma no max_connections=150.
"""
from __future__ import annotations


def close_tenant_after_task(*_args, **_kwargs) -> None:
    from core.db_config import close_tenant_connections

    close_tenant_connections()
