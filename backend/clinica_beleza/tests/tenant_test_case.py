"""
Base para testes de integração Clínica da Beleza.

Superadmin no default; tabelas clinica_beleza criadas no default via migrate no
setUpClass (MultiTenantRouter bloqueia no setup global do Django).
"""
from __future__ import annotations

from django.contrib.auth.models import User
from django.test import TransactionTestCase, override_settings

from config.db_router import MultiTenantRouter
from superadmin.authentication import invalidate_session_cache
from superadmin.models import Loja, PlanoAssinatura, TipoLoja
from tenants.middleware import set_current_loja_id, set_current_tenant_db


class ClinicaBelezaTestRouter(MultiTenantRouter):
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == 'default' and app_label == 'clinica_beleza':
            return True
        return super().allow_migrate(db, app_label, model_name, **hints)


_clinica_schema_ready = False


@override_settings(DATABASE_ROUTERS=['clinica_beleza.tests.tenant_test_case.ClinicaBelezaTestRouter'])
class ClinicaBelezaIntegrationTestCase(TransactionTestCase):
    """Duas lojas no public + clinica_beleza no default (isolamento por loja_id)."""

    @classmethod
    def setUpClass(cls):
        global _clinica_schema_ready
        super().setUpClass()
        if _clinica_schema_ready:
            return
        from django.core.management import call_command
        from django.db import connections

        with connections['default'].cursor() as cursor:
            cursor.execute("DELETE FROM django_migrations WHERE app = 'clinica_beleza'")
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'clinica_beleza_%'"
            )
            for (table_name,) in cursor.fetchall():
                cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
        call_command('migrate', 'clinica_beleza', database='default', verbosity=0)
        _clinica_schema_ready = True

    def setUp(self):
        uid = str(abs(hash(self.__class__.__name__ + self._testMethodName)))[:10]
        self.tipo = TipoLoja.objects.create(
            nome='Clínica da Beleza',
            slug=f'clb-int-{uid}',
            codigo=f'C{uid[:3]}',
        )
        self.plano = PlanoAssinatura.objects.create(
            nome='Integração',
            slug=f'plano-int-{uid}',
            preco_mensal=99,
        )
        self.owner = User.objects.create_user(
            username=f'owner-{uid}@test.com',
            email=f'owner-{uid}@test.com',
            password='pass12345',
        )
        self.loja = Loja.objects.create(
            nome='Clínica Integração A',
            slug=f'clinica-a-{uid}',
            cpf_cnpj=f'66666666{uid[:6]}',
            tipo_loja=self.tipo,
            plano=self.plano,
            owner=self.owner,
            database_created=True,
        )
        self.loja_b = Loja.objects.create(
            nome='Clínica Integração B',
            slug=f'clinica-b-{uid}',
            cpf_cnpj=f'77777777{uid[:6]}',
            tipo_loja=self.tipo,
            plano=self.plano,
            owner=self.owner,
            database_created=True,
        )
        invalidate_session_cache(self.owner.id)
        self.activate_loja(self.loja)

    def tearDown(self):
        invalidate_session_cache(getattr(self, 'owner', None) and self.owner.id)
        set_current_tenant_db('default')
        set_current_loja_id(None)

    def activate_loja(self, loja: Loja) -> None:
        set_current_tenant_db('default')
        set_current_loja_id(loja.id)

    def api_client_as_owner(self):
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken

        from superadmin.session_manager import SessionManager

        invalidate_session_cache(self.owner.id)
        client = APIClient()
        token = str(RefreshToken.for_user(self.owner).access_token)
        sid = SessionManager.create_session(self.owner.id, token)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}', HTTP_X_SESSION_ID=sid)
        return client

    def tenant_headers(self, loja: Loja | None = None) -> dict[str, str]:
        loja = loja or self.loja
        return {
            'HTTP_X_LOJA_ID': str(loja.id),
            'HTTP_X_TENANT_SLUG': loja.slug,
        }
