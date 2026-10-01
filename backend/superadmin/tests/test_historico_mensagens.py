"""Mensagens de sucesso/erro do histórico de acessos."""
from types import SimpleNamespace

from django.test import SimpleTestCase

from superadmin.historico_mensagens import (
    mensagem_resultado,
    texto_erro_legivel,
    tipo_resultado,
)


class TextoErroLegivelTests(SimpleTestCase):
    def test_dict_python_da_api(self):
        self.assertEqual(
            texto_erro_legivel("{'error': 'Horário já ocupado para este profissional.'}"),
            "Horário já ocupado para este profissional.",
        )

    def test_json(self):
        self.assertEqual(
            texto_erro_legivel('{"error": "Selecione o profissional."}'),
            "Selecione o profissional.",
        )

    def test_vazio(self):
        self.assertEqual(texto_erro_legivel(""), "")

    def test_conflito_de_agenda_com_datetime_no_meio(self):
        bruto = (
            "{'conflict': True, 'server': {'id': 463, "
            "'title': 'BIANCA ORNELLAS DE ALMEIDA - TIRZEPATIDA DOSE DE 5 MG', "
            "'start': '2026-10-01T16:50:00-03:00', "
            "'end': datetime.datetime(2026, 10, 1, 17, 10, "
            "tzinfo=zoneinfo.ZoneInfo(key='America/Sao_Paulo')), "
            "'backgroundColor': '#22c55e', 'borde…"
        )
        self.assertEqual(
            texto_erro_legivel(bruto),
            "Este agendamento foi alterado em outro dispositivo. A edição não foi salva. "
            "Versão que permanece: BIANCA ORNELLAS DE ALMEIDA - TIRZEPATIDA DOSE DE 5 MG · 01/10/2026 16:50.",
        )

    def test_conflito_json_cancelado(self):
        self.assertEqual(
            texto_erro_legivel(
                '{"conflict": true, "resolution_hint": "server_cancelled", '
                '"server": {"title": "Consulta", "start": "2026-10-01T16:50:00-03:00", "status": "CANCELLED"}}'
            ),
            "Este agendamento está cancelado no servidor. A edição não foi salva. "
            "Versão que permanece: Consulta · 01/10/2026 16:50.",
        )


class TipoResultadoTests(SimpleTestCase):
    def test_sucesso(self):
        self.assertEqual(tipo_resultado(True, ""), "sucesso")

    def test_horario_ocupado_e_recusa(self):
        self.assertEqual(
            tipo_resultado(False, "{'error': 'Horário já ocupado para este profissional.'}"),
            "recusado",
        )

    def test_falha_interna(self):
        self.assertEqual(tipo_resultado(False, "Erro ao salvar agendamento."), "erro")


class MensagemResultadoTests(SimpleTestCase):
    def test_sucesso_com_recurso(self):
        obj = SimpleNamespace(
            sucesso=True,
            acao="criar",
            recurso="Agenda",
            erro="",
            get_acao_display=lambda: "Criar",
        )
        self.assertEqual(mensagem_resultado(obj), "Criar em agenda concluído.")

    def test_erro_ocupado(self):
        obj = SimpleNamespace(
            sucesso=False,
            acao="criar",
            recurso="Agenda",
            erro="{'error': 'Horário já ocupado para este profissional.'}",
            get_acao_display=lambda: "Criar",
        )
        self.assertEqual(
            mensagem_resultado(obj),
            "Horário já ocupado para este profissional.",
        )
