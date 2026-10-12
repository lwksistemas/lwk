"""Troca de plano e dia de vencimento na tabela do financeiro."""
from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from superadmin.models import FinanceiroLoja, Loja, PlanoAssinatura, TipoLoja
from superadmin.views.financeiro import FinanceiroLojaViewSet


class FinanceiroAlterarPlanoTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.superuser = User.objects.create_superuser("master", "master@lwk.test", "senha-teste")
        self.tipo = TipoLoja.objects.create(nome="Clínica Beleza", slug="clinica-beleza", codigo="CLIBEL")
        self.plano = PlanoAssinatura.objects.create(
            nome="Básico", slug="basico-fin", descricao="Básico", preco_mensal="99.90",
        )
        self.plano.tipos_loja.add(self.tipo)
        self.completo = PlanoAssinatura.objects.create(
            nome="Completo", slug="completo-fin", descricao="Completo", preco_mensal="199.90",
        )
        self.completo.tipos_loja.add(self.tipo)
        self.outro = PlanoAssinatura.objects.create(
            nome="CRM", slug="crm-fin", descricao="CRM", preco_mensal="7.00",
        )
        owner = User.objects.create_user("loja", "loja@lwk.test", "senha-teste")
        self.loja = Loja.objects.create(
            nome="Harmonis",
            slug="clinicaharmonis",
            cpf_cnpj="37302743000126",
            tipo_loja=self.tipo,
            plano=self.plano,
            owner=owner,
        )
        self.financeiro = FinanceiroLoja.objects.create(
            loja=self.loja,
            data_proxima_cobranca=date(2026, 12, 1),
            valor_mensalidade="99.90",
            dia_vencimento=1,
            asaas_payment_id="pay_teste",
        )

    def _post(self, action, data):
        request = self.factory.post("/api/superadmin/financeiro/", data, format="json")
        force_authenticate(request, user=self.superuser)
        view = FinanceiroLojaViewSet.as_view({"post": action})
        return view(request, pk=self.financeiro.id)

    def test_alterar_plano_atualiza_valor(self):
        res = self._post("alterar_plano", {"plano_id": self.completo.id})
        self.assertEqual(res.status_code, 200, getattr(res, "data", None))
        self.loja.refresh_from_db()
        self.financeiro.refresh_from_db()
        self.assertEqual(self.loja.plano_id, self.completo.id)
        self.assertEqual(str(self.financeiro.valor_mensalidade), "199.90")

    def test_recusa_plano_de_outro_tipo(self):
        res = self._post("alterar_plano", {"plano_id": self.outro.id})
        self.assertEqual(res.status_code, 400)
        self.loja.refresh_from_db()
        self.assertEqual(self.loja.plano_id, self.plano.id)

    def test_alterar_dia_vencimento(self):
        res = self._post("alterar_dia_vencimento", {"dia_vencimento": 15})
        self.assertEqual(res.status_code, 200, getattr(res, "data", None))
        self.financeiro.refresh_from_db()
        self.assertEqual(self.financeiro.dia_vencimento, 15)
        self.assertEqual(self.financeiro.data_proxima_cobranca.day, 15)

    def test_dia_invalido(self):
        res = self._post("alterar_dia_vencimento", {"dia_vencimento": 31})
        self.assertEqual(res.status_code, 400)
        self.financeiro.refresh_from_db()
        self.assertEqual(self.financeiro.dia_vencimento, 1)
