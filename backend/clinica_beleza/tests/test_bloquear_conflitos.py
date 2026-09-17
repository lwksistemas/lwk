"""Conflito de agenda não ocupa horário de cancelado/faltou."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from rules.agenda import STATUS_NAO_OCUPAM_HORARIO, bloquear_conflitos


def _inicio():
    return datetime(2026, 9, 17, 10, 11, 30, tzinfo=timezone.utc)


def _contexto(**extra):
    inicio = _inicio()
    dados = {
        "profissional": object(),
        "date": inicio,
        "date_end": inicio + timedelta(minutes=30),
        "appointment_id": None,
    }
    dados.update(extra)
    return dados


def _agendamento(status, minutos=30):
    inicio = _inicio()
    return SimpleNamespace(
        status=status,
        date=inicio,
        pk=9,
        get_duracao_efetiva=lambda: minutos,
    )


def _queryset_com(itens):
    qs = MagicMock()
    qs.exclude.return_value = qs
    qs.select_related.return_value = itens
    return qs


class BloquearConflitosTests(SimpleTestCase):
    def test_status_livres_sao_cancelado_e_faltou(self):
        self.assertEqual(STATUS_NAO_OCUPAM_HORARIO, ("CANCELLED", "NO_SHOW"))

    @patch("rules.agenda.Appointment.objects")
    def test_horario_cancelado_libera_o_slot(self, objects):
        objects.filter.return_value = _queryset_com([_agendamento("CANCELLED")])
        bloquear_conflitos(_contexto())

    @patch("rules.agenda.Appointment.objects")
    def test_faltou_libera_o_slot(self, objects):
        objects.filter.return_value = _queryset_com([_agendamento("NO_SHOW")])
        bloquear_conflitos(_contexto())

    @patch("rules.agenda.Appointment.objects")
    def test_agendado_no_mesmo_horario_continua_bloqueando(self, objects):
        objects.filter.return_value = _queryset_com([_agendamento("SCHEDULED")])
        with self.assertRaises(ValidationError) as ctx:
            bloquear_conflitos(_contexto())
        self.assertIn("ocupado", str(ctx.exception).lower())

    @patch("rules.agenda.Appointment.objects")
    def test_consulta_em_andamento_continua_bloqueando(self, objects):
        objects.filter.return_value = _queryset_com([_agendamento("IN_PROGRESS")])
        with self.assertRaises(ValidationError):
            bloquear_conflitos(_contexto())

    @patch("rules.agenda.Appointment.objects")
    def test_queryset_exclui_cancelado_e_faltou(self, objects):
        qs = _queryset_com([])
        objects.filter.return_value = qs
        bloquear_conflitos(_contexto())
        status_excluidos = [
            call.kwargs.get("status__in")
            for call in qs.exclude.call_args_list
        ]
        self.assertIn(STATUS_NAO_OCUPAM_HORARIO, status_excluidos)
