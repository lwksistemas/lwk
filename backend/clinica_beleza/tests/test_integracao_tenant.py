"""Smoke tests de integração — Clínica da Beleza em banco tenant isolado.

Cobrem fluxos corrigidos na auditoria: cadastros sem schema_ensure em request,
anamnese, retorno gratuito, comissão em pagamento só taxa de consulta e isolamento entre lojas.
"""
from decimal import Decimal

from django.utils import timezone

from clinica_beleza.consulta_service import finalizar_consulta
from clinica_beleza.models import (
    Appointment,
    Consulta,
    LocalAtendimento,
    Patient,
    PatientAnamnese,
    Professional,
    ProfessionalCommission,
)
from clinica_beleza.retorno_service import get_agenda_retorno_config

from .tenant_test_case import ClinicaBelezaIntegrationTestCase


class ClinicaBelezaTenantSmokeTests(ClinicaBelezaIntegrationTestCase):
    def test_cria_paciente_com_contexto_loja(self):
        patient = Patient.objects.create(nome="Maria Integração", loja_id=self.loja.id)
        self.assertEqual(Patient.objects.filter(pk=patient.pk).count(), 1)

        self.activate_loja(self.loja_b)
        self.assertEqual(Patient.objects.filter(pk=patient.pk).count(), 0)

    def test_api_post_paciente_sem_schema_ensure(self):
        client = self.api_client_as_owner()
        response = client.post(
            "/api/clinica-beleza/patients/",
            {
                "name": "João API Tenant",
                "phone": "16999998888",
                "active": True,
            },
            format="json",
            **self.tenant_headers(),
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(
            Patient.objects.filter(nome="JOÃO API TENANT").exists()
            or Patient.objects.filter(nome__icontains="João").exists(),
        )

    def test_api_anamnese_put_cria_registro(self):
        patient = Patient.objects.create(nome="Paciente Anamnese", loja_id=self.loja.id)
        client = self.api_client_as_owner()
        response = client.put(
            f"/api/clinica-beleza/patients/{patient.id}/anamnese/",
            {"queixa_principal": "Melasma"},
            format="json",
            **self.tenant_headers(),
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(PatientAnamnese.objects.filter(patient_id=patient.id).exists())

    def test_api_retorno_config_get(self):
        client = self.api_client_as_owner()
        response = client.get(
            "/api/clinica-beleza/retorno/config/",
            **self.tenant_headers(),
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertIn("retorno_consulta_ativo", response.json())

    def test_retorno_service_config_no_tenant(self):
        config = get_agenda_retorno_config(self.loja.id)
        self.assertIsNotNone(config)
        self.assertEqual(config.loja_id, self.loja.id)

    def test_finalizar_consulta_somente_taxa_gera_comissao(self):
        patient = Patient.objects.create(nome="Paciente Taxa", loja_id=self.loja.id)
        professional = Professional.objects.create(nome="Dra. Taxa", loja_id=self.loja.id)
        local = LocalAtendimento.objects.create(
            nome="Sala 1",
            valor_consulta=Decimal("150.00"),
            loja_id=self.loja.id,
        )
        ProfessionalCommission.objects.create(
            professional=professional,
            tipo="consulta",
            modo="percentual",
            valor=Decimal("30.00"),
            local_atendimento=local,
            loja_id=self.loja.id,
        )

        appt = Appointment.objects.create(
            date=timezone.now(),
            status="IN_PROGRESS",
            patient=patient,
            professional=professional,
            local_atendimento=local,
            loja_id=self.loja.id,
        )
        consulta = Consulta.objects.create(
            appointment=appt,
            patient=patient,
            professional=professional,
            status="IN_PROGRESS",
            data_inicio=timezone.now(),
            valor_consulta=Decimal("150.00"),
            local_atendimento=local,
            loja_id=self.loja.id,
        )

        finalizar_consulta(
            consulta,
            payment_method="CASH",
            mark_as_paid=True,
            amount=Decimal("150.00"),
        )

        consulta.refresh_from_db()
        payment = consulta.appointment.payment_set.first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, "PAID")
        self.assertGreater(payment.comissao_valor or Decimal(0), Decimal(0))
        self.assertEqual(payment.comissao_valor, Decimal("45.00"))

    def test_isolamento_entre_lojas_por_loja_id(self):
        self.activate_loja(self.loja)
        Patient.objects.create(nome="Só Loja A", loja_id=self.loja.id)
        self.assertEqual(Patient.objects.filter(loja_id=self.loja.id).count(), 1)

        self.activate_loja(self.loja_b)
        self.assertEqual(Patient.objects.filter(loja_id=self.loja.id).count(), 0)
        Patient.objects.create(nome="Só Loja B", loja_id=self.loja_b.id)
        self.assertEqual(Patient.objects.filter(loja_id=self.loja_b.id).count(), 1)
