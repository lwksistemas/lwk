"""Papel no CRM: vendedor comum não administra e não herda a loja inteira."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from crm_vendas.assinatura_publica_helpers import ip_cliente_assinatura
from crm_vendas.relatorio_comissao_workflow import extrair_ip_cliente
from crm_vendas.utils import vendedor_pode_atribuir
from crm_vendas.views_relatorio_comissao_admin import criar_relatorio_comissao_view


class FiltroSemVinculoTests(SimpleTestCase):
    @patch("crm_vendas.utils.usuario_administra_crm", return_value=False)
    @patch("crm_vendas.mixins.get_current_vendedor_id", return_value=None)
    def test_sem_vinculo_nao_ve_a_loja(self, *_):
        from crm_vendas.mixins import VendedorFilterMixin

        class FakeViewSet(VendedorFilterMixin):
            vendedor_filter_field = "vendedor_id"
            vendedor_filter_related = []
            request = MagicMock()

        qs = MagicMock()
        vazio = MagicMock()
        qs.none.return_value = vazio
        self.assertIs(FakeViewSet().filter_by_vendedor(qs), vazio)
        qs.none.assert_called_once()


class ComissaoAdminTests(SimpleTestCase):
    @patch("crm_vendas.utils.usuario_administra_crm", return_value=False)
    def test_vendedor_nao_cria_relatorio(self, _admin):
        request = APIRequestFactory().post("/relatorios-comissao/criar/", {}, format="json")
        user = MagicMock()
        user.is_authenticated = True
        force_authenticate(request, user=user)
        response = criar_relatorio_comissao_view(request)
        self.assertEqual(response.status_code, 403)


class AtribuicaoTests(SimpleTestCase):
    @patch("crm_vendas.utils.usuario_administra_crm", return_value=False)
    @patch("crm_vendas.utils.get_current_vendedor_id", return_value=5)
    def test_vendedor_nao_escolhe_outro(self, *_):
        self.assertFalse(vendedor_pode_atribuir(MagicMock(), 9))
        self.assertTrue(vendedor_pode_atribuir(MagicMock(), 5))

    @patch("crm_vendas.utils.usuario_administra_crm", return_value=True)
    def test_administrador_escolhe_qualquer(self, _admin):
        self.assertTrue(vendedor_pode_atribuir(MagicMock(), 9))


class IpDoProxyTests(SimpleTestCase):
    def test_usa_o_ultimo_endereco(self):
        request = MagicMock()
        request.META = {
            "HTTP_X_FORWARDED_FOR": "203.0.113.8, 201.23.81.50",
            "REMOTE_ADDR": "127.0.0.1",
        }
        self.assertEqual(extrair_ip_cliente(request), "201.23.81.50")
        self.assertEqual(ip_cliente_assinatura(request), "201.23.81.50")
