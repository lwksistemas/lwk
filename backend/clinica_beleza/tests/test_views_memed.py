"""Memed token — regressão de import settings."""
from unittest import TestCase
from unittest.mock import MagicMock, patch

from clinica_beleza.memed_impressao import aviso_timbrado_nao_aplicado
from clinica_beleza.memed_service import prescritor_liberado_na_memed
from clinica_beleza.views_memed import MemedTokenView


class PrescritorLiberadoNaMemedTest(TestCase):
    def test_em_analise_sem_termos_nao_libera(self):
        self.assertFalse(
            prescritor_liberado_na_memed(
                {"state": "ok", "status": "Em análise", "terms_accepted": False, "tem_token": True}
            )
        )

    def test_nao_cadastrado_nao_libera(self):
        self.assertFalse(
            prescritor_liberado_na_memed({"state": "nao_cadastrado", "label": "Não cadastrado"})
        )

    def test_ativo_com_termos_libera(self):
        self.assertTrue(
            prescritor_liberado_na_memed(
                {"state": "ok", "status": "Ativo", "terms_accepted": True, "tem_token": True}
            )
        )


class AvisoTimbradoNaoAplicadoTest(TestCase):
    def test_pendente_cita_nome_e_reaplicar(self):
        msg = aviso_timbrado_nao_aplicado(
            {
                "aplicados": 0,
                "total": 1,
                "detalhes": [
                    {"ok": False, "nome": "NAYARA", "error": "prescritor_pendente_memed"}
                ],
            }
        )
        self.assertIn("NAYARA", msg)
        self.assertIn("Reaplicar", msg)


class MemedTokenViewTest(TestCase):
    @patch("tenants.middleware.get_current_loja_id", return_value=None)
    @patch("clinica_beleza.views_memed.settings")
    def test_resolver_prescritor_id_usa_settings_sem_name_error(self, mock_settings, _loja):
        mock_settings.MEMED_PRESCRITOR_ID_PROD = "12345"
        mock_settings.MEMED_PRESCRITOR_ID = ""
        mock_settings.MEMED_DEFAULT_UF = "SP"

        request = MagicMock()
        request.query_params.get.return_value = None

        view = MemedTokenView()
        result = view._resolver_prescritor_id(request, env="production")

        self.assertEqual(result, "12345")

    @patch("tenants.middleware.get_current_loja_id", return_value=13)
    @patch("clinica_beleza.views_memed.settings")
    def test_loja_nao_usa_prescritor_global(self, mock_settings, _loja):
        mock_settings.MEMED_PRESCRITOR_ID_PROD = "prescritor-outra-clinica"
        mock_settings.MEMED_PRESCRITOR_ID = "prescritor-outra-clinica"

        request = MagicMock()
        request.query_params.get.return_value = None

        view = MemedTokenView()
        self.assertEqual(view._resolver_prescritor_id(request, env="production"), "")
