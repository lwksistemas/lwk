from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from clinica_beleza.texto_clinico_service import (
    TextoClinicoIndisponivel,
    limpar_texto_revisado,
    montar_mensagens,
    revisar_texto_clinico,
)


class TextoClinicoTests(SimpleTestCase):
    def test_instrucao_pede_para_nao_inventar_fato_clinico(self):
        mensagens = montar_mensagens("paciente relata dor", "Queixa principal")
        self.assertIn("Não invente", mensagens[0]["content"])
        self.assertIn("Queixa principal", mensagens[1]["content"])
        self.assertIn("paciente relata dor", mensagens[1]["content"])

    def test_limpa_cerca_de_codigo(self):
        self.assertEqual(
            limpar_texto_revisado("```\nPaciente relata cefaleia.\n```"),
            "Paciente relata cefaleia.",
        )

    @override_settings(LWK_TEXTO_IA_API_KEY="")
    def test_sem_chave_nao_chama_a_ia(self):
        with self.assertRaises(TextoClinicoIndisponivel):
            revisar_texto_clinico("texto", "Evolução")

    @override_settings(LWK_TEXTO_IA_API_KEY="chave-teste", LWK_TEXTO_IA_MODELO="")
    @patch("clinica_beleza.texto_clinico_service.requests.post")
    def test_devolve_o_texto_revisado(self, post):
        resposta = MagicMock()
        resposta.status_code = 200
        resposta.json.return_value = {
            "choices": [{"message": {"content": "Paciente relata cefaleia."}}],
        }
        post.return_value = resposta

        texto = revisar_texto_clinico("paciente relata dor de cabeca", "Evolução")

        self.assertEqual(texto, "Paciente relata cefaleia.")
        self.assertIn("generativelanguage.googleapis.com", post.call_args.args[0])
