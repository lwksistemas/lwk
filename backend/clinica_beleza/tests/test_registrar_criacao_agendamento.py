from datetime import datetime
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.agenda_service import registrar_criacao_agendamento


class RegistrarCriacaoAgendamentoTests(SimpleTestCase):
    def _appointment(self):
        appointment = MagicMock()
        appointment.id = 452
        appointment.patient_id = 10
        appointment.professional_id = 6
        appointment.date = datetime(2026, 10, 1, 18, 30)
        appointment.created_by_id = None
        return appointment

    def test_grava_o_login_e_audita(self):
        appointment = self._appointment()
        user = MagicMock()
        user.is_authenticated = True
        user.pk = 8
        user.username = "bruna"
        user.get_full_name.return_value = "Bruna Tucci"
        request = MagicMock()

        with patch("core.audit.registrar_audit_manual") as audit:
            registrar_criacao_agendamento(appointment, user, request=request)

        self.assertEqual(appointment.created_by_id, 8)
        appointment.save.assert_called_once_with(update_fields=["created_by_id"])
        audit.assert_called_once()
        self.assertEqual(audit.call_args.args[1], "agendamento_criado")
        self.assertEqual(audit.call_args.kwargs["detalhes"]["usuario_id"], 8)

    def test_sem_login_nao_inventa_autor(self):
        appointment = self._appointment()
        registrar_criacao_agendamento(appointment, None, request=None)
        self.assertIsNone(appointment.created_by_id)
        appointment.save.assert_not_called()
