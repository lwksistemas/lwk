"""Recuperação de senha de superadmin e suporte: link antes de trocar a senha."""
import re
from unittest.mock import patch
from urllib.parse import unquote

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from rest_framework import status as http_status

from superadmin.models import UsuarioSistema
from superadmin.services.sistema_password_recovery_service import SistemaPasswordRecoveryService


class SistemaPasswordRecoveryTest(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="admin_lwk",
            email="admin@lwk.test",
            password="senha-antiga",
            first_name="Admin",
        )
        UsuarioSistema.objects.create(user=self.user, tipo="superadmin", is_active=True)

    def _token_do_email(self, mensagem) -> str:
        corpo = mensagem.body or ""
        achado = re.search(r"token=(\S+)", corpo)
        self.assertIsNotNone(achado)
        return unquote(achado.group(1))

    @patch("core.email_delivery.send_prepared")
    def test_pedido_nao_troca_a_senha(self, mock_send):
        payload, code = SistemaPasswordRecoveryService().solicitar("admin@lwk.test", "superadmin")
        self.assertEqual(code, http_status.HTTP_200_OK)
        self.assertNotIn("email", payload)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("senha-antiga"))
        mock_send.assert_called_once()

    @patch("core.email_delivery.send_prepared")
    def test_email_inexistente_tem_a_mesma_resposta(self, mock_send):
        ok, _code = SistemaPasswordRecoveryService().solicitar("admin@lwk.test", "superadmin")
        ausente, code = SistemaPasswordRecoveryService().solicitar("ninguem@lwk.test", "superadmin")
        self.assertEqual(code, http_status.HTTP_200_OK)
        self.assertEqual(ok["message"], ausente["message"])
        self.assertEqual(mock_send.call_count, 1)

    @patch("core.email_delivery.send_prepared")
    def test_link_cria_senha_uma_vez(self, mock_send):
        SistemaPasswordRecoveryService().solicitar("admin@lwk.test", "superadmin")
        token = self._token_do_email(mock_send.call_args[0][0])
        payload, code = SistemaPasswordRecoveryService().confirmar(token)
        self.assertEqual(code, http_status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(payload["senha_provisoria"]))
        self.assertFalse(self.user.perfil_sistema.senha_foi_alterada)
        de_novo, code_de_novo = SistemaPasswordRecoveryService().confirmar(token)
        self.assertEqual(code_de_novo, http_status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("senha_provisoria", de_novo)
