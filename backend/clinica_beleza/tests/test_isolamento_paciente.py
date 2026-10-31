"""Dono da loja A não lê paciente, prontuário nem pagamento da loja B."""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import override_settings
from django.utils import timezone

from clinica_beleza.models import Appointment, Patient, Payment, Professional

from .tenant_test_case import ClinicaBelezaIntegrationTestCase

# A API de produção autentica o JWT antes do tenant. O cookie entra nessa
# autenticação; sem isso o slug da outra loja era aceito enquanto o usuário
# ainda parecia anônimo.
_MIDDLEWARE_API = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "superadmin.middleware.JWTAuthenticationMiddleware",
    "tenants.middleware.TenantMiddleware",
]


class IsolamentoPacienteFinanceiroTest(ClinicaBelezaIntegrationTestCase):
    def setUp(self):
        super().setUp()
        self.owner_b = User.objects.create_user(
            username=f"owner-b-{self.loja_b.id}@test.com",
            email=f"owner-b-{self.loja_b.id}@test.com",
            password="pass12345",
        )
        self.loja_b.owner = self.owner_b
        self.loja_b.save(update_fields=["owner"])

        self.activate_loja(self.loja)
        self.paciente_a = Patient.objects.create(
            nome="Paciente Loja A",
            cpf="11144477735",
            loja_id=self.loja.id,
        )
        self.activate_loja(self.loja_b)
        self.paciente_b = Patient.objects.create(
            nome="Paciente Loja B",
            cpf="52998224725",
            loja_id=self.loja_b.id,
        )
        profissional_b = Professional.objects.create(nome="Dra B", loja_id=self.loja_b.id)
        consulta_b = Appointment.objects.create(
            date=timezone.now(),
            status="COMPLETED",
            patient=self.paciente_b,
            professional=profissional_b,
            loja_id=self.loja_b.id,
        )
        self.pagamento_b = Payment.objects.create(
            appointment=consulta_b,
            amount=Decimal("321.45"),
            payment_method="CASH",
            status="PAID",
            notes="segredo-financeiro-loja-b",
            loja_id=self.loja_b.id,
        )
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken

        from superadmin.session_manager import SessionManager

        token = str(RefreshToken.for_user(self.owner).access_token)
        sid = SessionManager.create_session(self.owner.id, token)
        self.client_a = APIClient()
        self.client_a.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_SESSION_ID=sid)
        self.client_cookie = APIClient()
        self.client_cookie.cookies["lwk_access"] = token
        self.client_cookie.cookies["lwk_session"] = sid

    def test_dono_a_nao_le_paciente_prontuario_nem_pagamento_da_loja_b(self):
        lista = self.client_a.get(
            "/api/clinica-beleza/patients/?all=1",
            **self.tenant_headers(self.loja),
        )
        self.assertEqual(lista.status_code, 200, lista.content)
        nomes = [item["nome"].casefold() for item in lista.json()]
        self.assertIn("paciente loja a", nomes)
        self.assertNotIn("paciente loja b", nomes)

        detalhe_errado = self.client_a.get(
            f"/api/clinica-beleza/patients/{self.paciente_b.id}/",
            **self.tenant_headers(self.loja),
        )
        self.assertEqual(detalhe_errado.status_code, 404)
        self.assertNotIn(b"52998224725", detalhe_errado.content)

        prontuario_errado = self.client_a.get(
            f"/api/clinica-beleza/patients/{self.paciente_b.id}/prontuario/",
            **self.tenant_headers(self.loja),
        )
        self.assertEqual(prontuario_errado.status_code, 404)
        self.assertNotIn(b"paciente loja b", prontuario_errado.content.lower())

        pagamento_errado = self.client_a.get(
            f"/api/clinica-beleza/payments/{self.pagamento_b.id}/",
            **self.tenant_headers(self.loja),
        )
        self.assertEqual(pagamento_errado.status_code, 404)
        self.assertNotIn(b"segredo-financeiro-loja-b", pagamento_errado.content)

        for caminho in (
            f"/api/clinica-beleza/patients/{self.paciente_b.id}/",
            f"/api/clinica-beleza/patients/{self.paciente_b.id}/prontuario/",
            f"/api/clinica-beleza/payments/{self.pagamento_b.id}/",
            "/api/clinica-beleza/financeiro/resumo/",
        ):
            resposta = self.client_a.get(caminho, **self.tenant_headers(self.loja_b))
            self.assertIn(resposta.status_code, (403, 404), resposta.content)
            self.assertNotIn(b"paciente loja b", resposta.content.lower())
            self.assertNotIn(b"segredo-financeiro-loja-b", resposta.content)
            self.assertNotIn(b"52998224725", resposta.content)

        with override_settings(MIDDLEWARE=_MIDDLEWARE_API):
            for caminho in (
                f"/api/clinica-beleza/patients/{self.paciente_b.id}/",
                f"/api/clinica-beleza/patients/{self.paciente_b.id}/prontuario/",
                f"/api/clinica-beleza/payments/{self.pagamento_b.id}/",
                "/api/clinica-beleza/financeiro/resumo/",
                "/api/crm-vendas/busca/?q=ab",
            ):
                resposta = self.client_cookie.get(caminho, **self.tenant_headers(self.loja_b))
                self.assertEqual(resposta.status_code, 403, resposta.content)
                self.assertEqual(resposta.json().get("code"), "CROSS_STORE_ACCESS_DENIED")
                self.assertNotIn(b"paciente loja b", resposta.content.lower())
                self.assertNotIn(b"segredo-financeiro-loja-b", resposta.content)
                self.assertNotIn(b"52998224725", resposta.content)
