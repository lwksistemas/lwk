"""Atalho duplicado no cadastro público deve falhar com mensagem clara."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError

from superadmin.serializers.loja import LojaCreateSerializer


class LojaCreateAtalhoTests(SimpleTestCase):
    @patch("superadmin.serializers.loja.Loja.objects")
    def test_atalho_ja_usado(self, mock_objects):
        mock_objects.filter.return_value.exists.return_value = True
        ser = LojaCreateSerializer()
        with self.assertRaises(ValidationError) as ctx:
            ser.validate_atalho("felix")
        self.assertIn("já está em uso", str(ctx.exception).lower())
        self.assertIn("felix", str(ctx.exception).lower())

    @patch("superadmin.serializers.loja.Loja.objects")
    def test_atalho_livre(self, mock_objects):
        mock_objects.filter.return_value.exists.return_value = False
        ser = LojaCreateSerializer()
        self.assertEqual(ser.validate_atalho("clinica-felix"), "clinica-felix")
