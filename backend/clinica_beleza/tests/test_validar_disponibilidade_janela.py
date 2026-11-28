"""Disponibilidade considera a janela completa (duração), não só o início."""
from datetime import datetime, time, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase

from clinica_beleza.agenda_service import AgendaValidationError, validar_disponibilidade_janela

TZ = ZoneInfo("America/Sao_Paulo")


def _dt(h, m=0):
    return datetime(2026, 11, 27, h, m, tzinfo=TZ)  # sexta


class ValidarDisponibilidadeJanelaTests(SimpleTestCase):
    @patch("clinica_beleza.agenda_service.validar_expediente_profissional")
    @patch("clinica_beleza.agenda_service.validar_regras_agendamento")
    @patch("clinica_beleza.agenda_service.bloqueio_impede_agendamento", return_value=True)
    def test_bloqueio_na_janela_impede(self, _bloq, _regras, _exp):
        with self.assertRaises(AgendaValidationError) as ctx:
            validar_disponibilidade_janela(SimpleNamespace(id=1), _dt(10), _dt(11))
        self.assertIn("bloqueado", str(ctx.exception).lower())
        _regras.assert_not_called()

    @patch("clinica_beleza.agenda_service.validar_expediente_profissional")
    @patch("clinica_beleza.agenda_service.validar_regras_agendamento")
    @patch("clinica_beleza.agenda_service.bloqueio_impede_agendamento", return_value=False)
    def test_chama_regras_e_expediente_com_fim_da_duracao(self, _bloq, regras, expediente):
        inicio = _dt(10)
        fim = inicio + timedelta(minutes=90)
        prof = SimpleNamespace(id=7)
        validar_disponibilidade_janela(prof, inicio, fim, appointment_id=None)
        regras.assert_called_once_with("AGENDAMENTO_CRIADO", prof, inicio, fim, appointment_id=None)
        expediente.assert_called_once_with(prof, inicio, fim)

    @patch("clinica_beleza.protocolo_comercial.intervalos_fora_do_expediente")
    @patch("clinica_beleza.models.HorarioTrabalhoProfissional.objects.filter")
    def test_expediente_rejeita_quando_cruza_almoco(self, filter_horarios, fora):
        from clinica_beleza.agenda_service import validar_expediente_profissional

        horario = SimpleNamespace(
            dia_semana=4,  # sexta
            hora_entrada=time(8, 0),
            hora_saida=time(18, 0),
            intervalo_inicio=time(12, 0),
            intervalo_fim=time(13, 0),
            ativo=True,
        )
        filter_horarios.return_value = [horario]
        fora.return_value = [(_dt(12, 0), _dt(13, 0))]

        with self.assertRaises(AgendaValidationError) as ctx:
            validar_expediente_profissional(SimpleNamespace(id=1), _dt(11, 30), _dt(12, 30))
        self.assertIn("intervalo", str(ctx.exception).lower())
