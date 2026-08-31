"""Nome exibido no topo da clínica: profissional vinculado, senão nome do login."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.me_service import build_me_payload, resolve_user_display_name


class ResolveUserDisplayNameTests(SimpleTestCase):
    def test_prioriza_nome_do_profissional(self):
        user = SimpleNamespace(username="bruna.login", get_full_name=lambda: "Bruna Login")
        self.assertEqual(
            resolve_user_display_name(user, professional_nome="BRUNA TUCCI MARTINS"),
            "BRUNA TUCCI MARTINS",
        )

    def test_usa_nome_completo_quando_nao_ha_profissional(self):
        user = SimpleNamespace(username="admin", get_full_name=lambda: "Marina Ramos")
        self.assertEqual(resolve_user_display_name(user), "Marina Ramos")

    def test_usa_username_quando_nao_ha_nome(self):
        user = SimpleNamespace(username="clinicaharmonis", get_full_name=lambda: "")
        self.assertEqual(resolve_user_display_name(user), "clinicaharmonis")


class BuildMePayloadTests(SimpleTestCase):
    def test_sem_loja_usa_username(self):
        user = SimpleNamespace(username="dona", get_full_name=lambda: "", is_superuser=False)
        payload = build_me_payload(user, None)
        self.assertEqual(payload["user_display_name"], "dona")
        self.assertIsNone(payload["professional_id"])
        self.assertFalse(payload["is_administrador"])

    def test_usa_nome_do_profissional_vinculado(self):
        user = SimpleNamespace(username="bruna.login", get_full_name=lambda: "", id=9, is_superuser=False)
        pu = MagicMock(professional_id=3, perfil="profissional")
        qs = MagicMock()
        qs.filter.return_value.values_list.return_value.first.return_value = "BRUNA TUCCI MARTINS"
        with (
            patch("superadmin.models.ProfissionalUsuario.objects.filter", return_value=MagicMock(first=lambda: pu)),
            patch("superadmin.models.Loja.objects.filter", return_value=MagicMock(first=lambda: None)),
            patch("clinica_beleza.models.Professional.objects", qs),
        ):
            payload = build_me_payload(user, 6)
        self.assertEqual(payload["user_display_name"], "BRUNA TUCCI MARTINS")
        self.assertEqual(payload["professional_id"], 3)
        self.assertFalse(payload["is_administrador"])

    def test_owner_eh_administrador(self):
        user = SimpleNamespace(username="dona", get_full_name=lambda: "", id=4, is_superuser=False)
        loja = SimpleNamespace(owner_id=4)
        loja_qs = MagicMock()
        loja_qs.only.return_value.first.return_value = loja
        with (
            patch("superadmin.models.Loja.objects.filter", return_value=loja_qs),
            patch("superadmin.models.ProfissionalUsuario.objects.filter", return_value=MagicMock(first=lambda: None)),
        ):
            payload = build_me_payload(user, 6)
        self.assertTrue(payload["is_administrador"])

    def test_perfil_administrador(self):
        from superadmin.models import ProfissionalUsuario

        user = SimpleNamespace(username="admin.loja", get_full_name=lambda: "", id=8, is_superuser=False)
        pu = MagicMock(professional_id=None, perfil=ProfissionalUsuario.PERFIL_ADMINISTRADOR)
        with (
            patch("superadmin.models.Loja.objects.filter", return_value=MagicMock(first=lambda: None)),
            patch("superadmin.models.ProfissionalUsuario.objects.filter", return_value=MagicMock(first=lambda: pu)),
        ):
            payload = build_me_payload(user, 6)
        self.assertTrue(payload["is_administrador"])

    def test_superuser_eh_administrador(self):
        user = SimpleNamespace(username="root", get_full_name=lambda: "", id=1, is_superuser=True)
        payload = build_me_payload(user, None)
        self.assertTrue(payload["is_administrador"])
