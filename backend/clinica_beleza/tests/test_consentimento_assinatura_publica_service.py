"""Testes do resolver de token público do termo de consentimento."""
from unittest import TestCase
from unittest.mock import MagicMock, patch

from clinica_beleza.consentimento_assinatura_publica_service import (
    path_assinar_consentimento,
    resolver_assinatura_publica,
)


class ResolverAssinaturaPublicaTest(TestCase):
    def test_path_assinar_codifica_dois_pontos_do_token(self):
        self.assertEqual(
            path_assinar_consentimento("abc:def"),
            "/assinar-consentimento/abc%3Adef",
        )

    def test_token_invalido(self):
        adapter = MagicMock()
        adapter.get_modulo.return_value = "clinica_beleza"
        with patch(
            "core.assinatura_service.decodificar_token",
            return_value=None,
        ):
            payload, assinatura, err = resolver_assinatura_publica(adapter, "x")
        self.assertIsNone(payload)
        self.assertIsNone(assinatura)
        self.assertEqual(err, "Link inválido.")

    def test_reenvio_reaproveita_assinatura_pendente(self):
        adapter = MagicMock()
        adapter.get_modulo.return_value = "clinica_beleza"
        adapter.buscar_assinatura_por_token.return_value = None
        pendente = MagicMock()
        adapter.buscar_assinatura_pendente.return_value = pendente
        payload = {
            "loja_id": 6,
            "doc_id": 33,
            "tipo": "profissional",
            "modulo": "clinica_beleza",
        }
        with patch(
            "core.assinatura_service.decodificar_token",
            return_value=payload,
        ):
            got_payload, assinatura, err = resolver_assinatura_publica(adapter, "token-antigo")
        self.assertIsNone(err)
        self.assertIs(assinatura, pendente)
        self.assertEqual(got_payload["doc_id"], 33)
        adapter.buscar_assinatura_pendente.assert_called_once_with(33, "profissional")
