"""Memed token — regressão de import settings."""
from unittest import TestCase
from unittest.mock import MagicMock, patch

from clinica_beleza.memed_impressao import aviso_timbrado_nao_aplicado
from clinica_beleza.memed_service import prescritor_liberado_na_memed
from clinica_beleza.views_memed import (
    MemedTokenView,
    _normalizar_status_memed,
    mensagem_falha_token_memed,
    prescritor_demo_homologacao,
)


class NormalizarStatusMemedTest(TestCase):
    def test_inativo_normaliza(self):
        # Só "inativo" deve ser bloqueado no MemedTokenView.
        self.assertEqual(_normalizar_status_memed("Inativo"), "inativo")
        self.assertEqual(_normalizar_status_memed("  INATIVO "), "inativo")

    def test_em_analise_nao_vira_inativo(self):
        # "Em análise" (com acento) normaliza sem acento e NÃO é "inativo".
        self.assertEqual(_normalizar_status_memed("Em análise"), "em analise")
        self.assertNotEqual(_normalizar_status_memed("Em análise"), "inativo")

    def test_ativo_e_vazio(self):
        self.assertEqual(_normalizar_status_memed("Ativo"), "ativo")
        self.assertEqual(_normalizar_status_memed(None), "")
        self.assertEqual(_normalizar_status_memed(""), "")


class PrescritorLiberadoNaMemedTest(TestCase):
    def test_em_analise_sem_termos_libera(self):
        self.assertTrue(
            prescritor_liberado_na_memed(
                {"state": "ok", "status": "Em análise", "terms_accepted": False}
            )
        )

    def test_nao_cadastrado_nao_libera(self):
        self.assertFalse(
            prescritor_liberado_na_memed({"state": "nao_cadastrado", "label": "Não cadastrado"})
        )

    def test_ativo_com_termos_libera(self):
        self.assertTrue(
            prescritor_liberado_na_memed({"state": "ok", "status": "Ativo", "terms_accepted": True})
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
    @patch("clinica_beleza.views_memed.token.settings")
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
    @patch("clinica_beleza.views_memed.token.settings")
    def test_loja_nao_usa_prescritor_global(self, mock_settings, _loja):
        mock_settings.MEMED_PRESCRITOR_ID_PROD = "prescritor-outra-clinica"
        mock_settings.MEMED_PRESCRITOR_ID = "prescritor-outra-clinica"

        request = MagicMock()
        request.query_params.get.return_value = None

        view = MemedTokenView()
        self.assertEqual(view._resolver_prescritor_id(request, env="production"), "")


class PrescritorDemoHomologacaoTest(TestCase):
    def test_usa_demo_quando_medico_da_loja_nao_existe_na_homologacao(self):
        self.assertEqual(
            prescritor_demo_homologacao("integration", 404, "22239255889", "demo-id"),
            "demo-id",
        )

    def test_nao_usa_demo_em_producao(self):
        self.assertEqual(
            prescritor_demo_homologacao("production", 404, "22239255889", "demo-id"),
            "",
        )

    def test_nao_usa_demo_quando_memed_esta_fora(self):
        self.assertEqual(
            prescritor_demo_homologacao("integration", 503, "22239255889", "demo-id"),
            "",
        )


class MensagemFalhaTokenMemedTest(TestCase):
    def test_homologacao_indisponivel(self):
        msg = mensagem_falha_token_memed("integration", 503, "<html><title>503")
        self.assertIn("homologação", msg)
        self.assertIn("indisponível", msg)

    def test_erro_generico_quando_nao_e_queda(self):
        self.assertEqual(
            mensagem_falha_token_memed("integration", 401, '{"errors":[]}'),
            "Erro ao obter o token do prescritor na Memed.",
        )
