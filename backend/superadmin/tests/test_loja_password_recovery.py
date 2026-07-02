"""Testes de recuperação de senha da loja (slug vs atalho na URL)."""
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status as http_status

from superadmin.models import Loja, PlanoAssinatura, ProfissionalUsuario, TipoLoja
from superadmin.services.loja_password_recovery_service import (
    LojaPasswordRecoveryService,
    resolve_loja_user_for_password_recovery,
)


class LojaPasswordRecoveryServiceTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner_felix',
            email='owner@felix.test',
            password='old-pass',
        )
        self.tipo = TipoLoja.objects.create(nome='CRM Vendas', descricao='')
        self.plano = PlanoAssinatura.objects.create(
            nome='Básico',
            tipo_loja=self.tipo,
            valor_mensal=99,
            valor_anual=990,
        )
        self.loja = Loja.objects.create(
            nome='Felix Test',
            slug='41449198000172',
            atalho='felix',
            owner=self.owner,
            tipo_loja=self.tipo,
            plano=self.plano,
            cpf_cnpj='41449198000172',
            is_active=True,
        )

    @patch('core.email_delivery.send_prepared')
    def test_resolve_por_atalho_na_url(self, mock_send):
        payload, code = LojaPasswordRecoveryService().execute(
            'owner@felix.test',
            'felix',
        )

        self.assertEqual(code, http_status.HTTP_200_OK)
        self.assertIn('message', payload)
        mock_send.assert_called_once()
        self.loja.refresh_from_db()
        self.assertFalse(self.loja.senha_foi_alterada)
        self.assertTrue(self.loja.senha_provisoria)

    @patch('core.email_delivery.send_prepared')
    def test_recuperacao_marca_profissional_usuario_trocar_senha(self, mock_send):
        ProfissionalUsuario.objects.create(
            user=self.owner,
            loja=self.loja,
            professional_id=1,
            perfil=ProfissionalUsuario.PERFIL_ADMINISTRADOR,
            precisa_trocar_senha=False,
        )
        LojaPasswordRecoveryService().execute('owner@felix.test', 'felix')
        pu = ProfissionalUsuario.objects.get(user=self.owner, loja=self.loja)
        self.assertTrue(pu.precisa_trocar_senha)
        mock_send.assert_called_once()

    @patch('core.email_delivery.send_prepared')
    def test_recuperacao_por_email_profissional(self, mock_send):
        prof_user = User.objects.create_user(
            username='admin_harmonis',
            email='admin@harmonis.test',
            password='old-pass',
        )
        ProfissionalUsuario.objects.create(
            user=prof_user,
            loja=self.loja,
            professional_id=1,
            perfil=ProfissionalUsuario.PERFIL_ADMINISTRADOR,
            precisa_trocar_senha=False,
        )
        payload, code = LojaPasswordRecoveryService().execute(
            'admin@harmonis.test',
            'felix',
        )

        self.assertEqual(code, http_status.HTTP_200_OK)
        mock_send.assert_called_once()
        pu = ProfissionalUsuario.objects.get(user=prof_user, loja=self.loja)
        self.assertTrue(pu.precisa_trocar_senha)

    def test_resolve_profissional_por_email(self):
        prof_user = User.objects.create_user(
            username='recep',
            email='recep@harmonis.test',
            password='x',
        )
        ProfissionalUsuario.objects.create(
            user=prof_user,
            loja=self.loja,
            professional_id=2,
            perfil=ProfissionalUsuario.PERFIL_RECEPCIONISTA,
        )
        resolved = resolve_loja_user_for_password_recovery(self.loja, 'recep@harmonis.test')
        self.assertEqual(resolved, prof_user)

    def test_email_incorreto_nao_envia(self):
        with patch('core.email_delivery.send_prepared') as mock_send:
            payload, code = LojaPasswordRecoveryService().execute(
                'outro@email.test',
                'felix',
            )

        self.assertEqual(code, http_status.HTTP_200_OK)
        mock_send.assert_not_called()
