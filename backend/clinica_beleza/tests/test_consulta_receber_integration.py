"""Integração — POST /consultas/<id>/receber/ (total, parcial, procedimento extra)."""
from decimal import Decimal

from django.contrib.auth.models import User
from django.utils import timezone

from clinica_beleza.consulta_service import registrar_recebimento_consulta
from clinica_beleza.consulta_service.payment import _sincronizar_recebimento_apos_procedimento
from clinica_beleza.models import (
    Appointment,
    AppointmentProcedure,
    Consulta,
    Patient,
    Payment,
    Procedure,
    Professional,
)
from superadmin.authentication import invalidate_session_cache
from superadmin.models import ProfissionalUsuario

from .tenant_test_case import ClinicaBelezaIntegrationTestCase


class ConsultaReceberIntegrationTests(ClinicaBelezaIntegrationTestCase):
    def _criar_consulta_receber(self, *, valor=Decimal("200.00")):
        patient = Patient.objects.create(nome="Paciente Receber", loja_id=self.loja.id)
        professional = Professional.objects.create(nome="Dr. Receber", loja_id=self.loja.id)
        appt = Appointment.objects.create(
            date=timezone.now(),
            status="CONFIRMED",
            patient=patient,
            professional=professional,
            loja_id=self.loja.id,
        )
        consulta = Consulta.objects.create(
            appointment=appt,
            patient=patient,
            professional=professional,
            status="RECEBER",
            valor_consulta=valor,
            loja_id=self.loja.id,
        )
        return consulta

    def test_api_receber_total_vai_para_scheduled(self):
        consulta = self._criar_consulta_receber()
        client = self.api_client_as_owner()
        response = client.post(
            f"/api/clinica-beleza/consultas/{consulta.id}/receber/",
            {"payment_method": "PIX", "amount": "200", "mark_as_paid": True},
            format="json",
            **self.tenant_headers(),
        )
        self.assertEqual(response.status_code, 201, response.content)
        body = response.json()
        # Receber grava rascunho — só vira PAID no Financeiro ao finalizar
        self.assertEqual(body["payment"]["status"], "DRAFT")
        self.assertEqual(body["consulta"]["status"], "SCHEDULED")
        self.assertEqual(body["consulta"]["payment_status"], "PAID")

        consulta.refresh_from_db()
        self.assertEqual(consulta.status, "SCHEDULED")
        payment = Payment.objects.get(appointment=consulta.appointment)
        self.assertEqual(payment.status, "DRAFT")
        self.assertIsNone(payment.payment_date)
        self.assertTrue(payment.parcelas.exists())
        self.assertEqual(payment.saldo_devedor, Decimal(0))

    def test_api_receber_parcial_mantem_receber(self):
        consulta = self._criar_consulta_receber()
        client = self.api_client_as_owner()
        response = client.post(
            f"/api/clinica-beleza/consultas/{consulta.id}/receber/",
            {"payment_method": "CASH", "amount": "80", "mark_as_paid": False},
            format="json",
            **self.tenant_headers(),
        )
        self.assertEqual(response.status_code, 201, response.content)
        body = response.json()
        self.assertEqual(body["payment"]["status"], "DRAFT")
        self.assertEqual(body["consulta"]["status"], "RECEBER")
        self.assertEqual(body["consulta"]["payment_status"], "PARTIAL")

        consulta.refresh_from_db()
        self.assertEqual(consulta.status, "RECEBER")

    def test_api_estornar_pagamento_cancela_parcelas(self):
        consulta = self._criar_consulta_receber()
        client = self.api_client_as_owner()
        receber = client.post(
            f"/api/clinica-beleza/consultas/{consulta.id}/receber/",
            {"payment_method": "PIX", "amount": "200", "mark_as_paid": True},
            format="json",
            **self.tenant_headers(),
        )
        self.assertEqual(receber.status_code, 201, receber.content)

        response = client.post(
            f"/api/clinica-beleza/consultas/{consulta.id}/estornar-pagamento/",
            {},
            format="json",
            **self.tenant_headers(),
        )
        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        self.assertEqual(body["payment"]["status"], "PENDING")
        self.assertEqual(body["consulta"]["status"], "RECEBER")

        consulta.refresh_from_db()
        self.assertEqual(consulta.status, "RECEBER")
        payment = Payment.objects.get(appointment=consulta.appointment)
        self.assertEqual(payment.status, "PENDING")
        self.assertEqual(payment.amount, Decimal(0))
        self.assertEqual(payment.valor_pago_parcelas, Decimal(0))
        self.assertTrue(payment.parcelas.filter(status="CANCELLED").exists())

    def test_api_estornar_em_atendimento_mantem_in_progress(self):
        """Corrigir pagamento com consulta já iniciada não rebaixa para RECEBER (sumiria da fila)."""
        consulta = self._criar_consulta_receber()
        consulta.data_inicio = timezone.now()
        consulta.status = "IN_PROGRESS"
        consulta.save(update_fields=["data_inicio", "status", "updated_at"])
        consulta.appointment.status = "IN_PROGRESS"
        consulta.appointment.save(update_fields=["status", "updated_at"])

        client = self.api_client_as_owner()
        receber = client.post(
            f"/api/clinica-beleza/consultas/{consulta.id}/receber/",
            {"payment_method": "PIX", "amount": "200", "mark_as_paid": True},
            format="json",
            **self.tenant_headers(),
        )
        self.assertEqual(receber.status_code, 201, receber.content)
        self.assertEqual(receber.json()["consulta"]["status"], "IN_PROGRESS")

        response = client.post(
            f"/api/clinica-beleza/consultas/{consulta.id}/estornar-pagamento/",
            {},
            format="json",
            **self.tenant_headers(),
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["consulta"]["status"], "IN_PROGRESS")

        consulta.refresh_from_db()
        self.assertEqual(consulta.status, "IN_PROGRESS")

        fila = client.get(
            "/api/clinica-beleza/consultas/?fila=iniciar",
            **self.tenant_headers(),
        )
        self.assertEqual(fila.status_code, 200, fila.content)
        ids = [item["id"] for item in fila.json()["results"]]
        self.assertIn(consulta.id, ids)

    def test_api_estornar_bloqueia_consulta_finalizada(self):
        consulta = self._criar_consulta_receber()
        client = self.api_client_as_owner()
        client.post(
            f"/api/clinica-beleza/consultas/{consulta.id}/receber/",
            {"payment_method": "PIX", "amount": "200", "mark_as_paid": True},
            format="json",
            **self.tenant_headers(),
        )
        consulta.status = "COMPLETED"
        consulta.save(update_fields=["status", "updated_at"])

        response = client.post(
            f"/api/clinica-beleza/consultas/{consulta.id}/estornar-pagamento/",
            {},
            format="json",
            **self.tenant_headers(),
        )
        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("finalizada", response.json().get("error", "").lower())

    def test_finalizar_publica_draft_no_financeiro(self):
        from clinica_beleza.consulta_service import finalizar_consulta, registrar_recebimento_consulta

        consulta = self._criar_consulta_receber()
        consulta.data_inicio = timezone.now()
        consulta.status = "IN_PROGRESS"
        consulta.save(update_fields=["data_inicio", "status", "updated_at"])

        registrar_recebimento_consulta(
            consulta,
            payment_method="PIX",
            amount=Decimal(200),
            mark_as_paid=True,
        )
        payment = Payment.objects.get(appointment=consulta.appointment)
        self.assertEqual(payment.status, "DRAFT")

        finalizar_consulta(consulta, skip_estoque=True)
        payment.refresh_from_db()
        self.assertEqual(payment.status, "PAID")
        self.assertIsNotNone(payment.payment_date)

    def test_procedimento_extra_reabre_receber(self):
        consulta = self._criar_consulta_receber(valor=Decimal("100.00"))
        registrar_recebimento_consulta(
            consulta,
            payment_method="CASH",
            amount=Decimal(100),
            mark_as_paid=True,
        )
        consulta.refresh_from_db()
        self.assertEqual(consulta.status, "SCHEDULED")

        # Simula aumento do total (procedimento extra) via valor_consulta
        consulta.valor_consulta = Decimal("180.00")
        consulta.save(update_fields=["valor_consulta", "updated_at"])
        _sincronizar_recebimento_apos_procedimento(consulta)

        consulta.refresh_from_db()
        self.assertEqual(consulta.status, "RECEBER")
        payment = Payment.objects.get(appointment=consulta.appointment)
        self.assertEqual(payment.status, "DRAFT")
        self.assertGreater(payment.saldo_devedor, Decimal(0))

    def _consulta_com_procedimento(self, *, preco=Decimal("150.00")):
        consulta = self._criar_consulta_receber(valor=Decimal("0"))
        proc = Procedure.objects.create(
            nome="Injeção de vitaminas",
            preco=preco,
            duracao_minutos=30,
            loja_id=self.loja.id,
        )
        AppointmentProcedure.objects.create(
            appointment=consulta.appointment,
            procedure=proc,
            valor=preco,
            ordem=0,
            loja_id=self.loja.id,
        )
        return consulta

    def _api_client_as(self, user):
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken

        from superadmin.session_manager import SessionManager

        invalidate_session_cache(user.id)
        client = APIClient()
        token = str(RefreshToken.for_user(user).access_token)
        sid = SessionManager.create_session(user.id, token)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_SESSION_ID=sid)
        return client

    def test_admin_pode_alterar_valor_procedimento(self):
        consulta = self._consulta_com_procedimento()
        client = self.api_client_as_owner()
        response = client.post(
            f"/api/clinica-beleza/consultas/{consulta.id}/receber/",
            {
                "payment_method": "CASH",
                "amount": "80",
                "mark_as_paid": True,
                "valor_procedimentos": "80",
            },
            format="json",
            **self.tenant_headers(),
        )
        self.assertEqual(response.status_code, 201, response.content)
        linha = AppointmentProcedure.objects.get(appointment=consulta.appointment)
        self.assertEqual(linha.valor, Decimal("80.00"))
        self.assertEqual(response.json()["consulta"]["valor_procedimentos"], 80.0)
        payment = Payment.objects.get(appointment=consulta.appointment)
        self.assertEqual(payment.valor_total, Decimal("80.00"))

    def test_profissional_nao_pode_alterar_valor_procedimento(self):
        consulta = self._consulta_com_procedimento()
        user = User.objects.create_user("prof-receber@t.com", "prof-receber@t.com", "pass12345")
        ProfissionalUsuario.objects.create(
            user=user,
            loja=self.loja,
            professional_id=consulta.professional_id,
            perfil=ProfissionalUsuario.PERFIL_PROFISSIONAL,
        )
        client = self._api_client_as(user)
        response = client.post(
            f"/api/clinica-beleza/consultas/{consulta.id}/receber/",
            {
                "payment_method": "CASH",
                "amount": "80",
                "mark_as_paid": True,
                "valor_procedimentos": "80",
            },
            format="json",
            **self.tenant_headers(),
        )
        self.assertEqual(response.status_code, 403, response.content)
        linha = AppointmentProcedure.objects.get(appointment=consulta.appointment)
        self.assertEqual(linha.valor, Decimal("150.00"))
