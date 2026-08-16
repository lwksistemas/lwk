"""Lembretes 24h/2h — telefone da clínica e janela do job 2h."""
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from whatsapp.tasks import (
    _JANELA_2H_ANTES,
    _JANELA_2H_DEPOIS,
    _paciente_aceita_whatsapp,
    _telefone_paciente,
)
from whatsapp.services import enviar_lembrete_agendamento


class TelefonePacienteLembreteTest(SimpleTestCase):
    def test_usa_telefone_quando_nao_tem_phone(self):
        patient = SimpleNamespace(phone=None, telefone="16997438862", allow_whatsapp=True)
        self.assertEqual(_telefone_paciente(patient), "16997438862")
        self.assertTrue(_paciente_aceita_whatsapp(patient))

    def test_prefers_phone_quando_existe(self):
        patient = SimpleNamespace(phone="5516981402966", telefone="16997438862", allow_whatsapp=True)
        self.assertEqual(_telefone_paciente(patient), "5516981402966")

    def test_recusa_sem_telefone(self):
        patient = SimpleNamespace(phone=None, telefone="", allow_whatsapp=True)
        self.assertFalse(_paciente_aceita_whatsapp(patient))

    def test_recusa_allow_whatsapp_false(self):
        patient = SimpleNamespace(phone=None, telefone="16997438862", allow_whatsapp=False)
        self.assertFalse(_paciente_aceita_whatsapp(patient))

    @patch("whatsapp.services.send_whatsapp", return_value=(True, None))
    @patch("whatsapp.services.msg_lembrete", return_value="Lembrete")
    def test_enviar_lembrete_usa_campo_telefone(self, _msg, mock_send):
        agendamento = SimpleNamespace(
            patient=SimpleNamespace(phone=None, telefone="16997438862"),
        )
        ok, err = enviar_lembrete_agendamento(agendamento, config=SimpleNamespace())
        self.assertTrue(ok)
        self.assertIsNone(err)
        mock_send.assert_called_once()
        self.assertEqual(mock_send.call_args.kwargs["telefone"], "16997438862")


class JanelaLembrete2hTest(SimpleTestCase):
    def test_janela_maior_que_intervalo_do_job(self):
        largura = _JANELA_2H_DEPOIS - _JANELA_2H_ANTES
        self.assertGreaterEqual(largura, timedelta(minutes=30))
        self.assertEqual(_JANELA_2H_ANTES, timedelta(hours=1, minutes=40))
        self.assertEqual(_JANELA_2H_DEPOIS, timedelta(hours=2, minutes=20))
