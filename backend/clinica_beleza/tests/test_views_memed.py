"""Memed token — regressão de import settings."""
from unittest import TestCase
from unittest.mock import MagicMock, patch

from clinica_beleza.views_memed import MemedTokenView


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
