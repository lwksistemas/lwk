"""Preços por convênio: tabela do procedimento e PATCH na consulta."""
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from django.utils import timezone

from clinica_beleza.convenio_service import aplicar_precos_convenio_atendimento
from clinica_beleza.models import (
    Appointment,
    AppointmentProcedure,
    Consulta,
    Convenio,
    ConvenioProcedimentoPreco,
    Patient,
    Procedure,
    Professional,
)

from .tenant_test_case import ClinicaBelezaIntegrationTestCase


class AplicarPrecosConvenioAtendimentoTest(SimpleTestCase):
    @patch("clinica_beleza.convenio_service.resolver_preco_procedimento")
    def test_atualiza_valor_pela_tabela(self, mock_resolver):
        mock_resolver.return_value = Decimal("150.00")
        ap = MagicMock()
        ap.valor = Decimal("300.00")
        ap.procedure = MagicMock()
        appointment = MagicMock()
        appointment.appointment_procedures.select_related.return_value.all.return_value = [ap]

        changed = aplicar_precos_convenio_atendimento(appointment, MagicMock())

        self.assertTrue(changed)
        self.assertEqual(ap.valor, Decimal("150.00"))
        ap.save.assert_called_once_with(update_fields=["valor"])
        self.assertIsNone(appointment._valor_total_cache)

    def test_sem_agendamento_nao_quebra(self):
        self.assertFalse(aplicar_precos_convenio_atendimento(None))


class ConvenioPrecoConsultaIntegrationTests(ClinicaBelezaIntegrationTestCase):
    def _criar_consulta_com_procedimento(self, *, status="COMPLETED", preco_particular="300.00"):
        patient = Patient.objects.create(nome="Luiz Convenio", loja_id=self.loja.id)
        professional = Professional.objects.create(nome="Dra Nayara", loja_id=self.loja.id)
        procedure = Procedure.objects.create(
            nome="TIRZEPATIDA (DOSE MINIMA)",
            preco=Decimal(preco_particular),
            duracao_minutos=20,
            loja_id=self.loja.id,
        )
        particular = Convenio.objects.create(nome="Particular", loja_id=self.loja.id)
        familia = Convenio.objects.create(nome="Família/Funcionário", loja_id=self.loja.id)
        ConvenioProcedimentoPreco.objects.create(
            convenio=particular,
            procedure=procedure,
            modo="fixo",
            preco=Decimal(preco_particular),
            loja_id=self.loja.id,
        )
        ConvenioProcedimentoPreco.objects.create(
            convenio=familia,
            procedure=procedure,
            modo="fixo",
            preco=Decimal("150.00"),
            loja_id=self.loja.id,
        )
        now = timezone.now()
        appt = Appointment.objects.create(
            date=now,
            status="COMPLETED" if status == "COMPLETED" else "IN_PROGRESS",
            patient=patient,
            professional=professional,
            procedure=procedure,
            convenio=particular,
            loja_id=self.loja.id,
        )
        AppointmentProcedure.objects.create(
            appointment=appt,
            procedure=procedure,
            ordem=0,
            valor=Decimal(preco_particular),
            loja_id=self.loja.id,
        )
        consulta = Consulta.objects.create(
            appointment=appt,
            patient=patient,
            professional=professional,
            procedure=procedure,
            status=status,
            data_inicio=now,
            data_fim=now if status == "COMPLETED" else None,
            convenio=particular,
            loja_id=self.loja.id,
        )
        return consulta, familia, procedure

    def test_patch_convenio_aplica_preco_da_tabela(self):
        consulta, familia, _procedure = self._criar_consulta_com_procedimento()
        client = self.api_client_as_owner()
        response = client.patch(
            f"/api/clinica-beleza/consultas/{consulta.id}/",
            {"convenio": familia.id},
            format="json",
            **self.tenant_headers(),
        )
        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        self.assertEqual(body["convenio"], familia.id)
        self.assertEqual(body["convenio_name"], "Família/Funcionário")
        self.assertEqual(body["procedures_list"][0]["valor"], 150.0)

        consulta.refresh_from_db()
        consulta.appointment.refresh_from_db()
        self.assertEqual(consulta.convenio_id, familia.id)
        self.assertEqual(consulta.appointment.convenio_id, familia.id)
        linha = consulta.appointment.appointment_procedures.get()
        self.assertEqual(linha.valor, Decimal("150.00"))
