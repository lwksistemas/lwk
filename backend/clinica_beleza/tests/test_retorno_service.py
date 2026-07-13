"""Testes do serviço de retorno gratuito."""
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from clinica_beleza.models import (
    AgendaRetornoConfig,
    Appointment,
    Consulta,
    LocalAtendimento,
    Patient,
    Procedure,
    Professional,
    RetornoProcedimentoRegra,
)
from clinica_beleza.retorno_service import (
    aplicar_retorno_em_consulta,
    get_agenda_retorno_config,
    verificar_retorno,
    verificar_retorno_consulta,
    verificar_retorno_procedimento,
)

from .tenant_test_case import ClinicaBelezaIntegrationTestCase


class RetornoServiceTests(ClinicaBelezaIntegrationTestCase):
    def setUp(self):
        super().setUp()
        self.loja_id = self.loja.id
        self.patient = Patient.objects.create(nome="Paciente Teste", loja_id=self.loja_id)
        self.professional = Professional.objects.create(nome="Dr. Teste", loja_id=self.loja_id)
        self.procedure = Procedure.objects.create(
            nome="Botox",
            preco=Decimal("500.00"),
            duracao_minutos=30,
            loja_id=self.loja_id,
        )
        self.local = LocalAtendimento.objects.create(
            nome="Consultório 1",
            valor_consulta=Decimal("150.00"),
            loja_id=self.loja_id,
        )

    def _consulta_concluida(self, *, procedure=None, days_ago=5):
        appt = Appointment.objects.create(
            date=timezone.now() - timedelta(days=days_ago),
            status="COMPLETED",
            patient=self.patient,
            professional=self.professional,
            procedure=procedure or self.procedure,
            local_atendimento=self.local,
            loja_id=self.loja_id,
        )
        return Consulta.objects.create(
            appointment=appt,
            patient=self.patient,
            professional=self.professional,
            procedure=procedure or self.procedure,
            status="COMPLETED",
            data_fim=timezone.now() - timedelta(days=days_ago),
            valor_consulta=self.local.valor_consulta,
            local_atendimento=self.local,
            loja_id=self.loja_id,
        )

    def test_config_criada_automaticamente(self):
        config = get_agenda_retorno_config(self.loja_id)
        self.assertIsInstance(config, AgendaRetornoConfig)
        self.assertFalse(config.retorno_procedimento_ativo)
        self.assertFalse(config.retorno_consulta_ativo)

    def test_retorno_por_consulta_dentro_prazo(self):
        AgendaRetornoConfig.objects.filter(loja_id=self.loja_id).delete()
        AgendaRetornoConfig.objects.create(
            loja_id=self.loja_id,
            retorno_consulta_ativo=True,
            dias_retorno_consulta=30,
        )
        self._consulta_concluida(days_ago=10)
        result = verificar_retorno_consulta(self.patient.id, self.loja_id)
        self.assertIsNotNone(result)
        self.assertTrue(result.elegivel)
        self.assertEqual(result.tipo, "consulta")

    def test_retorno_por_procedimento_dentro_prazo(self):
        AgendaRetornoConfig.objects.filter(loja_id=self.loja_id).delete()
        AgendaRetornoConfig.objects.create(
            loja_id=self.loja_id,
            retorno_procedimento_ativo=True,
        )
        RetornoProcedimentoRegra.objects.create(
            procedure=self.procedure,
            dias_retorno=15,
            loja_id=self.loja_id,
        )
        self._consulta_concluida(days_ago=7)
        result = verificar_retorno_procedimento(
            self.patient.id,
            [self.procedure.id],
            self.loja_id,
        )
        self.assertIsNotNone(result)
        self.assertTrue(result.elegivel)
        self.assertEqual(result.tipo, "procedimento")

    def test_aplicar_retorno_zera_valor_consulta(self):
        AgendaRetornoConfig.objects.filter(loja_id=self.loja_id).delete()
        AgendaRetornoConfig.objects.create(
            loja_id=self.loja_id,
            retorno_consulta_ativo=True,
            dias_retorno_consulta=30,
        )
        self._consulta_concluida(days_ago=3)

        appt = Appointment.objects.create(
            date=timezone.now(),
            status="SCHEDULED",
            patient=self.patient,
            professional=self.professional,
            local_atendimento=self.local,
            loja_id=self.loja_id,
        )
        consulta = Consulta.objects.create(
            appointment=appt,
            patient=self.patient,
            professional=self.professional,
            status="SCHEDULED",
            valor_consulta=self.local.valor_consulta,
            local_atendimento=self.local,
            loja_id=self.loja_id,
        )
        aplicar_retorno_em_consulta(consulta, appt)
        consulta.refresh_from_db()
        self.assertTrue(consulta.retorno_gratuito)
        self.assertEqual(consulta.retorno_tipo, "consulta")
        self.assertEqual(consulta.valor_consulta, Decimal(0))

    def test_verificar_retorno_prioriza_procedimento(self):
        AgendaRetornoConfig.objects.filter(loja_id=self.loja_id).delete()
        AgendaRetornoConfig.objects.create(
            loja_id=self.loja_id,
            retorno_procedimento_ativo=True,
            retorno_consulta_ativo=True,
            dias_retorno_consulta=30,
        )
        RetornoProcedimentoRegra.objects.create(
            procedure=self.procedure,
            dias_retorno=20,
            loja_id=self.loja_id,
        )
        self._consulta_concluida(days_ago=5)
        result = verificar_retorno(self.patient.id, [self.procedure.id], self.loja_id)
        self.assertTrue(result.elegivel)
        self.assertEqual(result.tipo, "procedimento")
