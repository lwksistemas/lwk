"""Testa atualizar_prescritor (PATCH) da integração Memed.

Garante: external_id só na URL (não no corpo), board correto no payload,
e tratamento de 404 (prescritor inexistente).
"""
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings


def _prof():
    return SimpleNamespace(
        id=1,
        loja_id=6,
        nome="DRA. NAYARA DA SILVA DE SOUZA",
        cpf="369.716.458-98",
        email="nayarass03@hotmail.com",
        telefone="16997438862",
        data_nascimento=date(1988, 5, 3),
        sexo="F",
        conselho="COREN",
        registro_profissional="356480",
        conselho_uf="SP",
    )


@override_settings(MEMED_API_KEY="k", MEMED_SECRET_KEY="s")
class AtualizarPrescritorTest(SimpleTestCase):
    @patch("clinica_beleza.memed_service._aplicar_timbrado_automatico", lambda *a, **k: None)
    @patch("clinica_beleza.memed_service.requests.patch")
    def test_patch_envia_board_correto_sem_external_id_no_corpo(self, mock_patch):
        from clinica_beleza.memed_service import atualizar_prescritor

        resp = MagicMock()
        resp.ok = True
        resp.status_code = 200
        resp.text = "{}"
        mock_patch.return_value = resp

        out = atualizar_prescritor(_prof())
        self.assertTrue(out["ok"])
        self.assertEqual(out["external_id"], "lwk-loja6-prof1")

        # URL usa o external_id
        args, kwargs = mock_patch.call_args
        url = args[0] if args else kwargs.get("url", "")
        self.assertIn("/sinapse-prescricao/usuarios/lwk-loja6-prof1", url)

        # Corpo NÃO contém external_id; board correto (COREN)
        body = kwargs["json"]
        attrs = body["data"]["attributes"]
        self.assertNotIn("external_id", attrs)
        self.assertEqual(attrs["board"]["board_code"], "COREN")
        self.assertEqual(attrs["board"]["board_number"], "356480")
        self.assertEqual(attrs["board"]["board_state"], "SP")
        # Prefixo "DRA." removido do nome
        self.assertEqual(attrs["nome"], "NAYARA")

    @patch("clinica_beleza.memed_service.requests.patch")
    def test_patch_404_marca_not_found(self, mock_patch):
        from clinica_beleza.memed_service import atualizar_prescritor

        resp = MagicMock()
        resp.ok = False
        resp.status_code = 404
        resp.text = "not found"
        mock_patch.return_value = resp

        out = atualizar_prescritor(_prof())
        self.assertFalse(out["ok"])
        self.assertTrue(out["not_found"])

    def test_patch_sem_cpf_valido_skip(self):
        from clinica_beleza.memed_service import atualizar_prescritor

        prof = _prof()
        prof.cpf = "123"
        out = atualizar_prescritor(prof)
        self.assertEqual(out.get("skipped"), "sem_cpf_valido")
