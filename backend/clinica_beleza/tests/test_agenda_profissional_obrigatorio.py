from datetime import datetime

from django.test import SimpleTestCase

from clinica_beleza.agenda_service import AgendaValidationError, criar_agendamento
from clinica_beleza.serializers.appointments import AppointmentCreateSerializer


class TestAppointmentCreateProfessionalRequired(SimpleTestCase):
    def test_campo_profissional_obrigatorio_no_serializer(self):
        field = AppointmentCreateSerializer().fields["professional"]
        self.assertTrue(field.required)
        self.assertFalse(field.allow_null)

    def test_criar_agendamento_rejeita_sem_profissional(self):
        with self.assertRaises(AgendaValidationError) as ctx:
            criar_agendamento({"date": datetime(2026, 9, 16, 16, 45)})
        self.assertIn("profissional", ctx.exception.message.lower())
