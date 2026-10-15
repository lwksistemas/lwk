"""A lista do financeiro mostra cada loja uma vez, no banco da assinatura."""
from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase

from asaas_integration.models import AsaasCustomer, LojaAssinatura
from superadmin.financeiro_views.unificado import _assinaturas_unificado
from superadmin.models import FinanceiroLoja, Loja, PlanoAssinatura, TipoLoja


class AssinaturasUnificadasTest(TestCase):
    def setUp(self):
        self.tipo = TipoLoja.objects.create(nome="Clínica Uni", slug="clinica-uni", codigo="CLIUNI")
        self.plano = PlanoAssinatura.objects.create(
            nome="Básico Uni", slug="basico-uni", descricao="Básico", preco_mensal="99.90",
        )
        self.plano.tipos_loja.add(self.tipo)

    def _loja(self, nome, slug, documento, preferido, provedor_financeiro):
        owner = User.objects.create_user(slug, f"{slug}@lwk.test", "senha-teste")
        loja = Loja.objects.create(
            nome=nome,
            slug=slug,
            cpf_cnpj=documento,
            tipo_loja=self.tipo,
            plano=self.plano,
            owner=owner,
            provedor_boleto_preferido=preferido,
        )
        FinanceiroLoja.objects.create(
            loja=loja,
            data_proxima_cobranca=date(2026, 11, 10),
            valor_mensalidade="99.90",
            dia_vencimento=10,
            asaas_payment_id=f"pay-{slug}",
            provedor_boleto=provedor_financeiro,
            senha_enviada=True,
        )
        return loja

    def _assinatura_asaas(self, loja):
        cliente = AsaasCustomer.objects.create(
            asaas_id=f"cus-{loja.slug}",
            name=loja.nome,
            email=loja.owner.email,
            cpf_cnpj=loja.cpf_cnpj,
        )
        LojaAssinatura.objects.create(
            loja_slug=loja.slug,
            loja_nome=loja.nome,
            asaas_customer=cliente,
            plano_nome=self.plano.nome,
            plano_valor="99.90",
        )

    def test_troca_de_banco_nao_duplica_a_loja(self):
        harmoni = self._loja("Harmonis", "harmonis-uni", "37302743000126", "cora", "cora")
        felix = self._loja("Felix", "felix-uni", "41449198000172", "asaas", "asaas")
        felipe = self._loja("Felipe", "felipe-uni", "34787081845", "cora", "cora")
        self._assinatura_asaas(harmoni)
        self._assinatura_asaas(felix)

        itens = _assinaturas_unificado()
        por_slug = {}
        for item in itens:
            por_slug.setdefault(item["loja_slug"], []).append(item)

        self.assertEqual(len(por_slug["harmonis-uni"]), 1)
        self.assertTrue(str(por_slug["harmonis-uni"][0]["id"]).startswith("cora-"))
        self.assertEqual(por_slug["harmonis-uni"][0]["current_payment_data"]["provedor"], "cora")
        self.assertEqual(por_slug["harmonis-uni"][0]["cpf_cnpj"], "37302743000126")
        self.assertEqual(len(por_slug["felix-uni"]), 1)
        self.assertFalse(str(por_slug["felix-uni"][0]["id"]).startswith(("cora-", "mp-")))
        self.assertEqual(len(por_slug["felipe-uni"]), 1)
        self.assertEqual(por_slug["felipe-uni"][0]["current_payment_data"]["provedor"], "cora")
        self.assertEqual(len(itens), 3)
        self.assertNotIn("_preferido", itens[0])
        self.assertFalse(por_slug["felix-uni"][0]["assinatura_cancelada"])

    def test_lista_marca_assinatura_cancelada(self):
        from superadmin.financeiro_views.assinatura_cancelamento import cancelar_assinatura

        loja = self._loja("Life", "life-uni", "43229198000192", "asaas", "asaas")
        self._assinatura_asaas(loja)
        cancelar_assinatura(loja, loja.financeiro)

        item = next(row for row in _assinaturas_unificado() if row["loja_slug"] == "life-uni")
        self.assertTrue(item["assinatura_cancelada"])
