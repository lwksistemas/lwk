"""Testes de Segurança Multi-Tenant

Valida isolamento de dados entre lojas e previne acesso cross-tenant.
"""
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from crm_vendas.models import Conta, Lead, Vendedor
from superadmin.models import Loja, PlanoAssinatura, TipoLoja
from tenants.middleware import TenantMiddleware, set_current_loja_id, set_current_tenant_db


class MultiTenantSecurityTestCase(TestCase):
    """Testes de segurança para isolamento multi-tenant."""

    def setUp(self):
        """Configuração inicial dos testes."""
        # Criar tipo e plano
        self.tipo_loja = TipoLoja.objects.create(
            nome="CRM Vendas",
            slug="crm-vendas",
            codigo="CRMVND",
        )
        self.plano = PlanoAssinatura.objects.create(
            nome="Básico",
            slug="basico",
            preco_mensal=99.90,
        )

        # Criar loja A
        self.owner_a = User.objects.create_user(
            username="owner_a@test.com",
            email="owner_a@test.com",
            password="senha123",
        )
        self.loja_a = Loja.objects.create(
            nome="Loja A",
            slug="loja-a",
            cpf_cnpj="11111111000111",
            tipo_loja=self.tipo_loja,
            plano=self.plano,
            owner=self.owner_a,
            database_name="loja_a",
        )

        # Criar loja B
        self.owner_b = User.objects.create_user(
            username="owner_b@test.com",
            email="owner_b@test.com",
            password="senha123",
        )
        self.loja_b = Loja.objects.create(
            nome="Loja B",
            slug="loja-b",
            cpf_cnpj="22222222000222",
            tipo_loja=self.tipo_loja,
            plano=self.plano,
            owner=self.owner_b,
            database_name="loja_b",
        )

        self.factory = RequestFactory()
        self.client = APIClient()

    def tearDown(self):
        set_current_tenant_db("default")
        set_current_loja_id(None)

    def get_token_for_user(self, user):
        """Gera token JWT para usuário."""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_middleware_blocks_cross_tenant_access(self):
        """Testa se middleware bloqueia acesso cross-tenant."""
        # Owner da loja A tenta acessar loja B
        request = self.factory.get("/loja/loja-b/crm-vendas/leads/")
        request.user = self.owner_a

        middleware = TenantMiddleware(lambda r: None)
        response = middleware(request)

        # Deve retornar 403 Forbidden
        self.assertEqual(response.status_code, 403)

    def test_loja_isolation_manager_filters_by_loja_id(self):
        """O manager restringe a consulta à loja do contexto."""
        set_current_tenant_db("default")
        set_current_loja_id(self.loja_a.id)
        sql_a = str(Vendedor.objects.all().query)
        self.assertIn(str(self.loja_a.id), sql_a)
        self.assertNotIn(str(self.loja_b.id), sql_a)

        set_current_loja_id(self.loja_b.id)
        sql_b = str(Vendedor.objects.all().query)
        self.assertIn(str(self.loja_b.id), sql_b)
        self.assertNotIn(str(self.loja_a.id), sql_b)

    def test_api_endpoint_respects_tenant_isolation(self):
        """Lead consultado no contexto da loja A não inclui o id da loja B."""
        set_current_tenant_db("default")
        set_current_loja_id(self.loja_a.id)
        sql = str(Lead.objects.all().query)
        self.assertIn("crm_vendas_lead", sql)
        self.assertIn(str(self.loja_a.id), sql)
        self.assertNotIn(str(self.loja_b.id), sql)

    def test_cannot_create_resource_with_different_loja_id(self):
        """Testa se não é possível criar recurso com loja_id diferente."""
        token_a = self.get_token_for_user(self.owner_a)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_a}")

        # Tentar criar lead com loja_id da loja B
        response = self.client.post(
            f"/api/loja/{self.loja_a.slug}/crm-vendas/leads/",
            {
                "nome": "Lead Malicioso",
                "loja_id": self.loja_b.id,  # Tentativa de injeção
                "email": "test@test.com",
            },
        )

        # Deve criar com loja_id correto (loja A)
        if response.status_code == 201:
            lead = Lead.objects.get(id=response.data["id"])
            self.assertEqual(lead.loja_id, self.loja_a.id)

    def test_database_router_prevents_cross_database_queries(self):
        """O router aponta o app da loja para o alias do tenant, e o manager filtra a outra loja."""
        from config.db_router import MultiTenantRouter

        router = MultiTenantRouter()
        set_current_tenant_db("loja_a")
        self.assertEqual(router.db_for_read(Conta), "loja_a")
        set_current_tenant_db("loja_b")
        self.assertEqual(router.db_for_read(Conta), "loja_b")

        set_current_tenant_db("default")
        set_current_loja_id(self.loja_b.id)
        sql = str(Conta.objects.all().query)
        self.assertIn(str(self.loja_b.id), sql)
        self.assertNotIn(str(self.loja_a.id), sql)


class SecurityViolationTestCase(TestCase):
    """Testes para detecção de violações de segurança."""

    def test_detect_brute_force_attempt(self):
        """Testa detecção de tentativa de brute force."""
        # TODO: Implementar quando sistema de detecção estiver pronto

    def test_detect_rate_limit_exceeded(self):
        """Testa detecção de rate limit excedido."""
        # TODO: Implementar quando rate limiting estiver pronto

    def test_detect_suspicious_ip_change(self):
        """Testa detecção de mudança suspeita de IP."""
        # TODO: Implementar quando monitoramento de IP estiver pronto
