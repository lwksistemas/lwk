"""Garante que delete_user_raw limpa FKs reais (user_sessions / violações)."""
from django.contrib.auth import get_user_model
from django.test import TestCase

from superadmin.models import UserSession, ViolacaoSeguranca
from superadmin.utils import delete_user_raw

User = get_user_model()


class DeleteUserRawTests(TestCase):
    def test_remove_user_with_session_and_violacao(self):
        user = User.objects.create_user(username="orfaotest", email="orfaotest@example.com", password="x")
        UserSession.objects.create(
            user=user,
            session_id="sess-orfaotest-001",
            token_hash="hash-orfaotest-001",
        )
        ViolacaoSeguranca.objects.create(
            tipo="suspicious_pattern",
            criticidade="baixa",
            user=user,
            usuario_email=user.email,
            usuario_nome=user.username,
            descricao="teste órfão",
            ip_address="127.0.0.1",
        )

        delete_user_raw(user.id)

        self.assertFalse(User.objects.filter(id=user.id).exists())
        self.assertFalse(UserSession.objects.filter(session_id="sess-orfaotest-001").exists())
        violacao = ViolacaoSeguranca.objects.filter(usuario_email="orfaotest@example.com").first()
        self.assertIsNotNone(violacao)
        self.assertIsNone(violacao.user_id)
