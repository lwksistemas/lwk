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
        user = SimpleNamespace(username="dona", get_full_name=lambda: "")
        payload = build_me_payload(user, None)
        self.assertEqual(payload["user_display_name"], "dona")
        self.assertIsNone(payload["professional_id"])

    def test_usa_nome_do_profissional_vinculado(self):
        user = SimpleNamespace(username="bruna.login", get_full_name=lambda: "")
        pu = MagicMock(professional_id=3)
        qs = MagicMock()
        qs.filter.return_value.values_list.return_value.first.return_value = "BRUNA TUCCI MARTINS"
        with (
            patch("superadmin.models.ProfissionalUsuario.objects.filter", return_value=MagicMock(first=lambda: pu)),
            patch("clinica_beleza.models.Professional.objects", qs),
        ):
            payload = build_me_payload(user, 6)
        self.assertEqual(payload["user_display_name"], "BRUNA TUCCI MARTINS")
        self.assertEqual(payload["professional_id"], 3)
