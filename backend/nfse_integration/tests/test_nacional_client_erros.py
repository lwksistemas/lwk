"""Erros do NacionalClient não vazam detalhe técnico para a API."""
from unittest.mock import patch

from django.test import SimpleTestCase

from nfse_integration.nacional.client import NacionalClient


class NacionalClientErrosTest(SimpleTestCase):
    def test_emitir_inesperado_usa_mensagem_fixa(self):
        from decimal import Decimal

        client = NacionalClient(pfx_bytes=b"x", senha_pfx="s", ambiente="homologacao")
        with patch(
            "nfse_integration.nacional.client.construir_xml_dps",
            side_effect=RuntimeError("segredo-tecnico-xyz"),
        ):
            out = client.emitir_nfse(
                numero_dps=1,
                serie_dps="1",
                codigo_municipio_prestador="3543402",
                prestador_cnpj="12345678000199",
                prestador_inscricao_municipal="1",
                tomador_cpf_cnpj="12345678909",
                tomador_nome="A",
                descricao_servico="X",
                valor_servicos=Decimal("10.00"),
            )
        self.assertFalse(out.get("success"))
        self.assertEqual(out.get("error"), "Falha interna na emissão da NFS-e Nacional")
        self.assertNotIn("segredo-tecnico-xyz", out.get("error", ""))

    def test_formatar_erros_ignora_objeto_estranho(self):
        texto = NacionalClient._formatar_erros(
            [{"Codigo": "E1", "Descricao": "ok"}, object(), "aviso", 9],
        )
        self.assertIn("[E1] ok", texto)
        self.assertIn("aviso", texto)
        self.assertIn("9", texto)
        self.assertNotIn("object", texto)
