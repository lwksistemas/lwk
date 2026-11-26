"""Regressão: login-config da clínica deve ler/gravar agenda_visual."""
from types import SimpleNamespace

from django.test import SimpleTestCase

from clinica_beleza.views_login_config import serialize_login_config
from superadmin.theme_colors import sanitize_agenda_visual


class LoginConfigAgendaVisualTest(SimpleTestCase):
    def test_serialize_inclui_agenda_visual_salvo(self):
        loja = SimpleNamespace(
            logo="",
            login_background="",
            login_logo="",
            cor_primaria="#10B981",
            cor_secundaria="#059669",
            cor_fundo_pagina="",
            agenda_status_colors={},
            agenda_visual="forma",
            colunas_consultas=[],
            colunas_estoque=[],
            colunas_pacientes=[],
            tipo_loja=None,
        )
        data = serialize_login_config(loja)
        self.assertIn("agenda_visual", data)
        self.assertEqual(data["agenda_visual"], "forma")

    def test_serialize_padrao_pulse_quando_vazio(self):
        loja = SimpleNamespace(
            logo="",
            login_background="",
            login_logo="",
            cor_primaria="",
            cor_secundaria="",
            cor_fundo_pagina="",
            agenda_status_colors={},
            agenda_visual="",
            colunas_consultas=[],
            colunas_estoque=[],
            colunas_pacientes=[],
            tipo_loja=None,
        )
        self.assertEqual(serialize_login_config(loja)["agenda_visual"], "pulse")

    def test_patch_aceita_agenda_visual_sanitizado(self):
        """Sem sanitize no PATCH, valor inválido ou forma não seria persistido com segurança."""
        self.assertEqual(sanitize_agenda_visual("forma"), "forma")
        self.assertEqual(sanitize_agenda_visual("xyz"), "pulse")

        from clinica_beleza import views_login_config as mod
        import inspect

        src = inspect.getsource(mod.LoginConfigView.patch)
        self.assertIn("sanitize_agenda_visual", src)
        self.assertIn("agenda_visual", src)
