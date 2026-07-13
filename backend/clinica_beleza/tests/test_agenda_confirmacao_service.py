"""Confirmação de agendamento — CLIENT_CONFIRMED pelo link não deve criar consulta."""
from unittest import TestCase
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from clinica_beleza.agenda_confirmacao_service import (
    processar_resposta_confirmacao,
    url_confirmacao_frontend,
)
from clinica_beleza.consulta_service import sync_consulta_from_appointment_status


class SyncConsultaConfirmacaoTest(TestCase):
    def test_client_confirmed_nao_cria_consulta(self):
        appt = MagicMock()
        result = sync_consulta_from_appointment_status(appt, "CLIENT_CONFIRMED", "SCHEDULED")
        self.assertIsNone(result)

    def test_phone_confirmed_nao_cria_consulta(self):
        appt = MagicMock()
        result = sync_consulta_from_appointment_status(appt, "PHONE_CONFIRMED", "SCHEDULED")
        self.assertIsNone(result)


class ProcessarRespostaConfirmacaoTest(TestCase):
    @patch("clinica_beleza.agenda_service.atualizar_agendamento")
    @patch("clinica_beleza.agenda_confirmacao_service._configurar_tenant")
    @patch("clinica_beleza.agenda_confirmacao_service.decodificar_token_confirmacao")
    @patch("clinica_beleza.models.Appointment")
    def test_confirmar_pelo_link_usa_client_confirmed(
        self,
        mock_appointment_model,
        mock_decode,
        mock_tenant,
        mock_atualizar,
    ):
        mock_tenant.return_value = None
        mock_decode.return_value = {"loja_id": 15, "doc_id": 99}
        appointment = MagicMock(status="SCHEDULED", id=99)
        mock_appointment_model.objects.select_related.return_value.filter.return_value.first.return_value = appointment
        updated = MagicMock(status="CLIENT_CONFIRMED", id=99)
        mock_atualizar.return_value = MagicMock(appointment=updated)

        result = processar_resposta_confirmacao("token", "confirmar")

        self.assertTrue(result.ok)
        self.assertEqual(result.status, "CLIENT_CONFIRMED")
        mock_atualizar.assert_called_once()
        self.assertEqual(mock_atualizar.call_args.kwargs["new_status"], "CLIENT_CONFIRMED")


class UrlConfirmacaoFrontendTest(SimpleTestCase):
    @override_settings(FRONTEND_URL="https://beta.lwksistemas.com.br")
    @patch("core.short_link.build_short_url", side_effect=lambda url, **_: url)
    def test_token_com_dois_pontos_e_codificado_na_url(self, _short):
        url = url_confirmacao_frontend("parte1:parte2:assinatura")
        self.assertIn("/confirmar-agendamento/parte1%3Aparte2%3Aassinatura", url)
        self.assertNotIn("/confirmar-agendamento/parte1:parte2", url)
