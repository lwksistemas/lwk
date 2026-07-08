"""Testes — sync agenda CONFIRMED → consulta RECEBER."""
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.consulta_service.sync import (
    _status_inicial_consulta,
    sync_consulta_from_appointment_status,
)


class StatusInicialConsultaTest(SimpleTestCase):
    def test_receber_quando_ha_valor(self):
        appointment = MagicMock(valor_total=Decimal('100'))
        defaults = {'valor_consulta': Decimal('50'), 'retorno_gratuito': False}
        self.assertEqual(_status_inicial_consulta(appointment, defaults), 'RECEBER')

    def test_scheduled_quando_gratuito(self):
        appointment = MagicMock(valor_total=Decimal('0'))
        defaults = {'valor_consulta': Decimal('0'), 'retorno_gratuito': False}
        self.assertEqual(_status_inicial_consulta(appointment, defaults), 'SCHEDULED')

    def test_scheduled_quando_retorno_gratuito(self):
        appointment = MagicMock(valor_total=Decimal('200'))
        defaults = {'valor_consulta': Decimal('50'), 'retorno_gratuito': True}
        self.assertEqual(_status_inicial_consulta(appointment, defaults), 'SCHEDULED')


class SyncConsultaConfirmedTest(SimpleTestCase):
    @patch('clinica_beleza.consulta_service.payment.garantir_conta_pendente_consulta')
    @patch('clinica_beleza.consulta_service.Consulta')
    @patch('clinica_beleza.consulta_service.sync._consulta_defaults_from_appointment')
    def test_confirmed_cria_consulta_receber(self, mock_defaults, mock_consulta_model, mock_conta):
        appointment = MagicMock(valor_total=Decimal('0'))
        mock_defaults.return_value = {
            'valor_consulta': Decimal('80'),
            'retorno_gratuito': False,
        }
        consulta = MagicMock(status='RECEBER')
        mock_consulta_model.objects.get_or_create.return_value = (consulta, True)

        result = sync_consulta_from_appointment_status(appointment, 'CONFIRMED', 'SCHEDULED')

        self.assertIs(result, consulta)
        kwargs = mock_consulta_model.objects.get_or_create.call_args.kwargs
        self.assertEqual(kwargs['defaults']['status'], 'RECEBER')
        mock_conta.assert_called_once_with(consulta)

    @patch('clinica_beleza.consulta_service.Consulta')
    @patch('clinica_beleza.consulta_service.sync._consulta_defaults_from_appointment')
    def test_confirmed_nao_altera_em_andamento(self, mock_defaults, mock_consulta_model):
        appointment = MagicMock(valor_total=Decimal('0'))
        mock_defaults.return_value = {'valor_consulta': Decimal('80'), 'retorno_gratuito': False}
        consulta = MagicMock(status='IN_PROGRESS')
        mock_consulta_model.objects.get_or_create.return_value = (consulta, False)

        sync_consulta_from_appointment_status(appointment, 'CONFIRMED', 'SCHEDULED')

        consulta.save.assert_not_called()
