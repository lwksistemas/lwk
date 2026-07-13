"""Testes do cancelamento de NFS-e (loja/CRM)."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from nfse_integration.cancelamento_loja import cancelar_nfse_loja


class CancelarNFSeLojaTests(SimpleTestCase):
    def _nfse(self, *, provedor="issnet", status="emitida", numero_nf="151", numero_rps=155):
        nfse = MagicMock()
        nfse.provedor = provedor
        nfse.status = status
        nfse.numero_nf = numero_nf
        nfse.numero_rps = numero_rps
        nfse.pode_cancelar.return_value = status == "emitida"
        return nfse

    def _config(self, *, provedor_nf="issnet", certificado=True):
        config = MagicMock()
        config.provedor_nf = provedor_nf
        config.inscricao_municipal = "12345"
        config.issnet_serie_rps = "1"
        if certificado:
            config.issnet_certificado = b"pfx"
        else:
            config.issnet_certificado = None
            config.nacional_certificado = None
        return config

    def _loja(self):
        loja = MagicMock()
        loja.id = 1
        loja.cpf_cnpj = "41449198000172"
        loja.inscricao_municipal = ""
        loja.nome = "Felix Representações"
        return loja

    def test_nao_cancela_local_sem_certificado(self):
        nfse = self._nfse()
        config = self._config(certificado=False)
        loja = self._loja()

        resultado = cancelar_nfse_loja(loja, config, nfse, "151", "Erro na emissão")

        self.assertFalse(resultado["success"])
        self.assertIn("Certificado", resultado["error"])
        self.assertNotEqual(nfse.status, "cancelada")

    def test_nao_cancela_local_provedor_nacional(self):
        nfse = self._nfse(provedor="nacional")
        config = self._config(provedor_nf="nacional")
        loja = self._loja()

        resultado = cancelar_nfse_loja(loja, config, nfse, "151", "Motivo")

        self.assertFalse(resultado["success"])
        self.assertIn("API Nacional", resultado["error"])
        nfse.save.assert_not_called()

    def test_nao_cancela_local_quando_issnet_rejeita(self):
        nfse = self._nfse()
        config = self._config()
        loja = self._loja()
        client = MagicMock()
        client.cancelar_nfse.return_value = {"success": False, "error": "[E123] Rejeitado"}
        client.__enter__ = MagicMock(return_value=client)
        client.__exit__ = MagicMock(return_value=False)

        with patch("nfse_integration.cancelamento_loja.issnet_client_loja", return_value=client), patch(
            "nfse_integration.cancelamento_loja.consultar_nfse_cancelada_issnet",
            return_value=False,
        ):
            resultado = cancelar_nfse_loja(loja, config, nfse, "151", "Erro na emissão")

        self.assertFalse(resultado["success"])
        self.assertIn("Rejeitado", resultado["error"])
        nfse.save.assert_not_called()

    def test_cancela_somente_apos_sucesso_issnet(self):
        nfse = self._nfse()
        config = self._config()
        loja = self._loja()
        client = MagicMock()
        client.cancelar_nfse.return_value = {"success": True}
        client.__enter__ = MagicMock(return_value=client)
        client.__exit__ = MagicMock(return_value=False)

        with patch("nfse_integration.cancelamento_loja.issnet_client_loja", return_value=client):
            with patch("nfse_integration.cancelamento_loja.notificar_cancelamento_nfse"):
                resultado = cancelar_nfse_loja(loja, config, nfse, "151", "Erro na emissão")

        self.assertTrue(resultado["success"])
        self.assertEqual(nfse.status, "cancelada")
        nfse.save.assert_called_once()
