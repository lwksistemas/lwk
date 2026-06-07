"""Testes de recuperação de senha da loja (slug vs atalho na URL)."""
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status as http_status

from superadmin.models import Loja, PlanoAssinatura, TipoLoja
from superadmin.services.loja_password_recovery_service import LojaPasswordRecoveryService


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

    def test_email_incorreto_nao_envia(self):
        with patch('core.email_delivery.send_prepared') as mock_send:
            payload, code = LojaPasswordRecoveryService().execute(
                'outro@email.test',
                'felix',
            )

        self.assertEqual(code, http_status.HTTP_200_OK)
        mock_send.assert_not_called()
