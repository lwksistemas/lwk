"""Login público por CPF/CNPJ não grava o documento em log."""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from superadmin.models import Loja, PlanoAssinatura, TipoLoja


class BuscarPorDocumentoLogTest(TestCase):
    def setUp(self):
        tipo = TipoLoja.objects.create(nome="Clínica", slug="clinica-bpd", codigo="CBPD")
        plano = PlanoAssinatura.objects.create(nome="Básico", slug="basico-bpd", preco_mensal=99)
        owner = User.objects.create_user(
            username="owner-bpd@test.com", email="owner-bpd@test.com", password="senha12345",
        )
        self.cnpj = "11222333000181"
        Loja.objects.create(
            nome="Clínica Teste BPD",
            slug="clinica-bpd-login",
            cpf_cnpj=self.cnpj,
            tipo_loja=tipo,
            plano=plano,
            owner=owner,
            is_active=True,
        )
        self.client = APIClient()

    def test_encontra_loja_sem_logar_cnpj(self):
        with self.assertLogs("superadmin.views.loja.viewset", level="INFO") as captured:
            res = self.client.get(
                "/api/superadmin/lojas/buscar-por-documento/",
                {"documento": self.cnpj},
            )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["slug"], "clinica-bpd-login")
        joined = " ".join(captured.output)
        self.assertNotIn(self.cnpj, joined)

    def test_nao_encontrada_sem_logar_documento(self):
        with self.assertLogs("superadmin.views.loja.viewset", level="WARNING") as captured:
            res = self.client.get(
                "/api/superadmin/lojas/buscar-por-documento/",
                {"documento": "00000000000000"},
            )
        self.assertEqual(res.status_code, 404)
        joined = " ".join(captured.output)
        self.assertNotIn("00000000000000", joined)
