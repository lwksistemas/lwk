"""Guard de tipo_loja nas rotas CRM."""
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from crm_vendas.permissions import IsCrmTipoLoja, loja_e_crm


class LojaECrmTests(SimpleTestCase):
    def test_slug_crm_ok(self):
        self.assertTrue(loja_e_crm(SimpleNamespace(tipo_loja=SimpleNamespace(slug="crm-vendas"))))

    def test_slug_inventado_negado(self):
        self.assertFalse(loja_e_crm(SimpleNamespace(tipo_loja=SimpleNamespace(slug="crm-api-xyz"))))

    def test_slug_clinica_negado(self):
        self.assertFalse(loja_e_crm(SimpleNamespace(tipo_loja=SimpleNamespace(slug="clinica-beleza"))))

    def test_slug_salao_negado(self):
        self.assertFalse(loja_e_crm(SimpleNamespace(tipo_loja=SimpleNamespace(slug="salao-cabeleireiro"))))


class IsCrmTipoLojaTests(SimpleTestCase):
    def setUp(self):
        self.perm = IsCrmTipoLoja()

    def test_superuser_ok(self):
        request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True, is_superuser=True))
        self.assertTrue(self.perm.has_permission(request, None))

    def test_sem_loja_nao_bloqueia(self):
        request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True, is_superuser=False))
        with (
            patch("core.loja_request.resolve_loja_id_from_request", return_value=None),
            patch("tenants.middleware.get_current_loja_id", return_value=None),
        ):
            self.assertTrue(self.perm.has_permission(request, None))

    def test_clinica_negada(self):
        loja = SimpleNamespace(tipo_loja=SimpleNamespace(slug="clinica-beleza"))
        request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True, is_superuser=False))
        with (
            patch("core.loja_request.resolve_loja_id_from_request", return_value=3),
            patch("tenants.middleware.get_current_loja_id", return_value=3),
            patch("crm_vendas.permissions.Loja.objects.select_related") as mock_sr,
        ):
            mock_sr.return_value.filter.return_value.first.return_value = loja
            self.assertFalse(self.perm.has_permission(request, None))

    def test_crm_ok(self):
        loja = SimpleNamespace(tipo_loja=SimpleNamespace(slug="crm-vendas"))
        request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True, is_superuser=False))
        with (
            patch("core.loja_request.resolve_loja_id_from_request", return_value=3),
            patch("tenants.middleware.get_current_loja_id", return_value=3),
            patch("crm_vendas.permissions.Loja.objects.select_related") as mock_sr,
        ):
            mock_sr.return_value.filter.return_value.first.return_value = loja
            self.assertTrue(self.perm.has_permission(request, None))
