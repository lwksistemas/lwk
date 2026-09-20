"""Token de PDF público: cache por hash, sem chave em claro, sem uso único."""
from django.core.cache import cache
from django.test import SimpleTestCase, override_settings

from clinica_beleza.public_pdf import (
    PREFIX_ORCAMENTO,
    _chave_hash,
    gravar_pdf_publico,
    ler_pdf_publico,
)


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class PublicPdfTokenTest(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def test_grava_hash_nao_o_token_em_claro(self):
        token = gravar_pdf_publico(PREFIX_ORCAMENTO, {"orcamento_id": 9, "pdf": b"%PDF"})
        self.assertIsNone(cache.get(f"{PREFIX_ORCAMENTO}_{token}"))
        self.assertEqual(
            cache.get(_chave_hash(PREFIX_ORCAMENTO, token)),
            {"orcamento_id": 9, "pdf": b"%PDF"},
        )

    def test_ler_pelo_token_da_url(self):
        token = gravar_pdf_publico(PREFIX_ORCAMENTO, {"orcamento_id": 3, "pdf": b"abc"})
        self.assertEqual(
            ler_pdf_publico(PREFIX_ORCAMENTO, token),
            {"orcamento_id": 3, "pdf": b"abc"},
        )

    def test_token_errado_nao_acha(self):
        gravar_pdf_publico(PREFIX_ORCAMENTO, {"orcamento_id": 1, "pdf": b"x"})
        self.assertIsNone(ler_pdf_publico(PREFIX_ORCAMENTO, "token-inventado"))

    def test_nao_le_chave_legada_em_claro(self):
        cache.set(f"{PREFIX_ORCAMENTO}_legado32charsxxxxxxxxxxxxxxxx", {"orcamento_id": 4, "pdf": b"old"}, 60)
        self.assertIsNone(ler_pdf_publico(PREFIX_ORCAMENTO, "legado32charsxxxxxxxxxxxxxxxx"))

    def test_segunda_leitura_ainda_vale(self):
        token = gravar_pdf_publico(PREFIX_ORCAMENTO, {"orcamento_id": 2, "pdf": b"pdf"})
        self.assertIsNotNone(ler_pdf_publico(PREFIX_ORCAMENTO, token))
        self.assertIsNotNone(ler_pdf_publico(PREFIX_ORCAMENTO, token))

    def test_token_vazio_ou_enorme_e_none(self):
        self.assertIsNone(ler_pdf_publico(PREFIX_ORCAMENTO, ""))
        self.assertIsNone(ler_pdf_publico(PREFIX_ORCAMENTO, "x" * 201))
