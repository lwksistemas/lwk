"""Testes — procedimentos durante consulta em atendimento."""
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.consulta_procedimentos_service import (
    adicionar_procedimento_consulta,
    remover_procedimento_consulta,
)


class ConsultaProcedimentosServiceTest(SimpleTestCase):
  def test_adicionar_bloqueia_fora_de_atendimento(self):
    consulta = MagicMock()
    consulta.status = 'SCHEDULED'
    with self.assertRaisesMessage(ValueError, 'em atendimento'):
      adicionar_procedimento_consulta(consulta, 1)

  def test_remover_bloqueia_apos_finalizar(self):
    consulta = MagicMock()
    consulta.status = 'COMPLETED'
    with self.assertRaisesMessage(ValueError, 'finalizar'):
      remover_procedimento_consulta(consulta, 1)

  @patch('clinica_beleza.consulta_procedimentos_service._sincronizar_recebimento_apos_procedimento')
  @patch('clinica_beleza.consulta_procedimentos_service.Procedure')
  @patch('clinica_beleza.consulta_procedimentos_service.AppointmentProcedure')
  @patch('clinica_beleza.consulta_procedimentos_service.resolver_preco_procedimento')
  def test_adicionar_cria_item_com_preco(self, mock_preco, mock_ap_model, mock_proc_model, mock_reabrir):
    mock_preco.return_value = Decimal('150.00')
    procedure = MagicMock()
    procedure.id = 7
    procedure.termo_consentimento_ativo = False
    procedure.termo_consentimento = ''
    mock_proc_model.objects.get.return_value = procedure

    appointment = MagicMock()
    appointment.appointment_procedures.filter.return_value.exists.return_value = False
    appointment.appointment_procedures.aggregate.return_value = {'m': 0}
    appointment.procedure_id = None

    consulta = MagicMock()
    consulta.status = 'IN_PROGRESS'
    consulta.appointment = appointment
    consulta.loja_id = 1
    consulta.procedure_id = None

    created = MagicMock()
    mock_ap_model.objects.create.return_value = created

    result = adicionar_procedimento_consulta(consulta, 7)

    self.assertIs(result, created)
    mock_ap_model.objects.create.assert_called_once()
    kwargs = mock_ap_model.objects.create.call_args.kwargs
    self.assertEqual(kwargs['procedure'], procedure)
    self.assertEqual(kwargs['valor'], Decimal('150.00'))
    mock_reabrir.assert_called_once_with(consulta)

  @patch('clinica_beleza.consulta_procedimentos_service._sincronizar_recebimento_apos_procedimento')
  @patch('clinica_beleza.consulta_procedimentos_service.Procedure')
  @patch('clinica_beleza.consulta_procedimentos_service.AppointmentProcedure')
  @patch('clinica_beleza.consulta_procedimentos_service.resolver_preco_procedimento')
  def test_adicionar_permitido_status_receber(self, mock_preco, mock_ap_model, mock_proc_model, _mock_reabrir):
    mock_preco.return_value = Decimal('150.00')
    procedure = MagicMock()
    procedure.id = 8
    procedure.termo_consentimento_ativo = False
    procedure.termo_consentimento = ''
    mock_proc_model.objects.get.return_value = procedure

    appointment = MagicMock()
    appointment.appointment_procedures.filter.return_value.exists.return_value = False
    appointment.appointment_procedures.aggregate.return_value = {'m': 0}
    appointment.procedure_id = None

    consulta = MagicMock()
    consulta.status = 'RECEBER'
    consulta.appointment = appointment
    consulta.loja_id = 1
    consulta.procedure_id = None

    created = MagicMock()
    mock_ap_model.objects.create.return_value = created

    result = adicionar_procedimento_consulta(consulta, 8)

    self.assertIs(result, created)
    mock_ap_model.objects.create.assert_called_once()
