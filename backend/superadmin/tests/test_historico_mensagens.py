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
