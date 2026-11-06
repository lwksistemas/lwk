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


class ConsultaSemVinculoTests(SimpleTestCase):
    def _request(self, method, path, data=None):
        factory = APIRequestFactory()
        request = factory.post(path, data or {}, format="json") if method == "post" else factory.get(path)
        user = MagicMock()
        user.is_authenticated = True
        user.id = 1
        force_authenticate(request, user=user)
        return request

    def test_busca_sem_vinculo_fica_vazia(self):
        from crm_vendas.views_crm_busca import _aplicar_filtro_vendedor

        qs = MagicMock()
        vazio = MagicMock()
        qs.none.return_value = vazio
        pedido = MagicMock()
        with patch("crm_vendas.views_crm_busca.usuario_administra_crm", return_value=False), patch(
            "crm_vendas.views_crm_busca.vendedor_tem_controle_qualidade", return_value=False,
        ):
            self.assertIs(_aplicar_filtro_vendedor(qs, None, pedido), vazio)

    @patch("crm_vendas.views_crm_me_dashboard._is_owner_loja", return_value=False)
    @patch("crm_vendas.views_crm_me_dashboard.get_current_loja_id", return_value=4)
    @patch("crm_vendas.views_crm_me_dashboard.usuario_administra_crm", return_value=False)
    @patch("crm_vendas.views_crm_me_dashboard.get_current_vendedor_id", return_value=None)
    def test_dashboard_sem_vinculo_fica_vazio(self, *_):
        from crm_vendas.views_crm_me_dashboard import dashboard_data

        response = dashboard_data(self._request("get", "/dashboard/"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["leads"], 0)
        self.assertEqual(response.data["receita"], 0)

    @patch("crm_vendas.views_financeiro.resumo_financeiro_crm", return_value={"receitas_pagas": 0})
    @patch("crm_vendas.views_financeiro.garantir_grupos_padrao")
    @patch("crm_vendas.views_financeiro.get_current_loja_id", return_value=4)
    @patch("crm_vendas.views_financeiro.is_owner", return_value=False)
    @patch("crm_vendas.views_financeiro.usuario_administra_crm", return_value=False)
    @patch("crm_vendas.views_financeiro.get_current_vendedor_id", return_value=None)
    def test_resumo_financeiro_sem_vinculo_nao_soma_a_loja(self, _vid, _admin, _dono, _loja, _grupos, resumo):
        from crm_vendas.views_financeiro import financeiro_crm_resumo

        response = financeiro_crm_resumo(self._request("get", "/financeiro/resumo/"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resumo.call_args.args[1], -1)

    @patch("crm_vendas.models.Vendedor.objects")
    @patch("crm_vendas.relatorios_financeiro.gerar_relatorio_financeiro_vendedor")
    @patch("crm_vendas.views_financeiro.get_current_loja_id", return_value=4)
    @patch("crm_vendas.views_financeiro.vendedor_tem_controle_qualidade", return_value=False)
    @patch("crm_vendas.views_financeiro.usuario_administra_crm", return_value=False)
    @patch("crm_vendas.views_financeiro.is_owner", return_value=False)
    @patch("crm_vendas.views_financeiro.get_current_vendedor_id", return_value=None)
    def test_pdf_financeiro_sem_vinculo_nao_pega_a_loja(self, _vid, _dono, _admin, _qualidade, _loja, gerar, _vendedores):
        from io import BytesIO

        from crm_vendas.views_financeiro import financeiro_crm_relatorio_pdf

        gerar.return_value = BytesIO(b"%PDF")
        response = financeiro_crm_relatorio_pdf(self._request("post", "/financeiro/pdf/", {"periodo": "mes_atual"}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(gerar.call_args.kwargs["vendedor_id"], -1)

    @patch("crm_vendas.views_relatorios.get_current_loja_id", return_value=4)
    @patch("crm_vendas.views_relatorios.vendedor_tem_controle_qualidade", return_value=False)
    @patch("crm_vendas.views_relatorios.usuario_administra_crm", return_value=False)
    @patch("crm_vendas.views_relatorios.get_current_vendedor_id", return_value=None)
    def test_relatorio_sem_vinculo_recusado(self, *_):
        from crm_vendas.views_relatorios import gerar_relatorio

        response = gerar_relatorio(self._request("post", "/relatorios/", {"tipo": "vendas_total"}))
        self.assertEqual(response.status_code, 403)
