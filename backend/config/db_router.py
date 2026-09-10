"""Database Router para Multi-Tenant com 3 bancos isolados:
1. default - Super Admin (schema: public)
2. suporte - Sistema de Suporte (schema: suporte)
3. loja_* - Bancos dinâmicos por loja (schemas: loja_*)

Com PostgreSQL, usa schemas isolados no mesmo banco.
Com SQLite local, usa arquivos separados.
"""
from functools import lru_cache


@lru_cache(maxsize=1)
def _apps_permitidos_schema_loja() -> frozenset[str]:
    """Apps que podem criar tabela em schema loja_*.

    Sem esta lista, allow_migrate=True para QUALQUER app no tenant — o Django
    recria tabelas legado (asaas, admin, token_blacklist) depois do
    «Limpar legado».
    """
    from superadmin.services.database_schema_service import TIPO_LOJA_EXTRA_APPS

    apps = {"contenttypes", "auth", "stores", "products"}
    for extra in TIPO_LOJA_EXTRA_APPS.values():
        apps.update(extra)
    apps.update(MultiTenantRouter.loja_apps)
    return frozenset(apps)


class MultiTenantRouter:
    """Router que direciona queries para o banco correto baseado no app/model
    """

    # Apps que usam o banco de suporte
    suporte_apps = frozenset({"suporte"})

    # Apps com dados por loja (schema loja_* / SQLite db_loja_*).
    # Manter alinhado a: modelos com LojaIsolationMixin + LojaIsolationManager em */models.py
    # e INSTALLED_APPS. Novo módulo tenant: incluir aqui + migrations só em loja_* (allow_migrate).
    loja_apps = frozenset(
        (
            "cabeleireiro",
            "clinica_beleza",
            "crm_vendas",
            "hotel",
            "nfse_integration",
            "products",
            "stores",
            "whatsapp",
        ),
    )

    # Apps permitidos no alias suporte (schema PostgreSQL `suporte`)
    suporte_dependency_apps = frozenset({"auth", "contenttypes", "sessions"})

    def db_for_read(self, model, **hints):
        """Direciona leitura para o banco correto"""
        if model._meta.app_label in self.suporte_apps:
            return "suporte"

        # Usar get_current_tenant_db do middleware (mesmo storage de thread)
        from tenants.middleware import get_current_tenant_db
        tenant_db = get_current_tenant_db()
        if tenant_db and tenant_db != "default" and model._meta.app_label in self.loja_apps:
            return tenant_db
        return "default"

    def db_for_write(self, model, **hints):
        """Direciona escrita para o banco correto"""
        if model._meta.app_label in self.suporte_apps:
            return "suporte"

        from tenants.middleware import get_current_tenant_db
        tenant_db = get_current_tenant_db()
        if tenant_db and tenant_db != "default" and model._meta.app_label in self.loja_apps:
            return tenant_db
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        """Permite relações apenas dentro do mesmo banco"""
        db1 = self.db_for_read(obj1.__class__)
        db2 = self.db_for_read(obj2.__class__)
        return db1 == db2

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Controla quais apps podem migrar em quais bancos"""
        if app_label in self.suporte_apps:
            return db == "suporte"

        if db == "suporte":
            return app_label in self.suporte_dependency_apps

        if db.startswith("loja_") or db == "loja_template":
            return app_label in _apps_permitidos_schema_loja()

        if app_label in self.loja_apps:
            return False

        return db == "default"
