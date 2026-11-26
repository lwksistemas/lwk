"""Guard de tipo_loja: loja CRM/salão não passa nas permissões da clínica."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.permissions import IsClinicaLojaMember, loja_e_clinica


class LojaEClinicaTests(SimpleTestCase):
    def test_slug_clinica_ok(self):
        loja = SimpleNamespace(tipo_loja=SimpleNamespace(slug="clinica-beleza", nome=""))
        self.assertTrue(loja_e_clinica(loja))

    def test_slug_crm_negado(self):
        loja = SimpleNamespace(tipo_loja=SimpleNamespace(slug="crm-vendas", nome="CRM"))
        self.assertFalse(loja_e_clinica(loja))

    def test_slug_salao_negado(self):
        loja = SimpleNamespace(tipo_loja=SimpleNamespace(slug="salao-cabeleireiro", nome="Salão"))
        self.assertFalse(loja_e_clinica(loja))


class IsClinicaLojaMemberTipoTests(SimpleTestCase):
    def test_loja_crm_negada(self):
        loja = MagicMock()
        loja.owner_id = 1
        loja.tipo_loja = SimpleNamespace(slug="crm-vendas", nome="CRM")
        request = SimpleNamespace(
            user=SimpleNamespace(is_authenticated=True, is_superuser=False, id=1),
        )

        with (
            patch("clinica_beleza.views_base.resolve_loja_id_from_request", return_value=7),
            patch("clinica_beleza.permissions.Loja.objects.select_related") as mock_sr,
        ):
            mock_sr.return_value.filter.return_value.first.return_value = loja
            perm = IsClinicaLojaMember()
            self.assertFalse(perm.has_permission(request, None))

    def test_loja_clinica_owner_ok(self):
        loja = MagicMock()
        loja.owner_id = 1
        loja.tipo_loja = SimpleNamespace(slug="clinica-beleza", nome="Clínica da Beleza")
        request = SimpleNamespace(
            user=SimpleNamespace(is_authenticated=True, is_superuser=False, id=1),
        )

        with (
            patch("clinica_beleza.views_base.resolve_loja_id_from_request", return_value=7),
            patch("clinica_beleza.permissions.Loja.objects.select_related") as mock_sr,
        ):
            mock_sr.return_value.filter.return_value.first.return_value = loja
            perm = IsClinicaLojaMember()
            self.assertTrue(perm.has_permission(request, None))
