"""Exception genérica do ISSNet não vaza str(exc) para a API."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from nfse_integration.mensagens_erro import ERR_NFSE_CANCELAMENTO, ERR_NFSE_CONSULTA


class MensagensErroIssnetTest(SimpleTestCase):
    @patch("nfse_integration.issnet_superadmin.certificado_configurado", return_value=True)
    @patch("nfse_integration.issnet_superadmin.issnet_nacional_client_superadmin")
    def test_cancelamento_superadmin_nacional_usa_mensagem_fixa(self, client_fn, _cert):
        from nfse_integration.issnet_superadmin import _cancelar_emitida_padrao_nacional

        client = MagicMock()
        client.cancelar_nfse.side_effect = RuntimeError("cert /tmp/segredo.pem")
        client_fn.return_value = client
        nf = SimpleNamespace(numero_nf="1", numero_rps=1, serie_rps="1", xml_nfse="", codigo_verificacao="")
        out = _cancelar_emitida_padrao_nacional(nf, SimpleNamespace(), "1", "erro")
        self.assertFalse(out["success"])
        self.assertEqual(out["error"], ERR_NFSE_CANCELAMENTO)
        self.assertNotIn("segredo", out["error"])

    @patch("nfse_integration.issnet_status_sync.logger")
    def test_status_sync_consulta_rps_nao_propaga_excecao(self, _log):
        from nfse_integration.issnet_status_sync import consultar_nfse_cancelada_issnet

        client = MagicMock()
        client.consultar_nfse_por_rps.side_effect = RuntimeError("host interno")
        client.consultar_url_nfse.return_value = {"success": False, "cancelada": False}
        ok = consultar_nfse_cancelada_issnet(
            client,
            numero_nf="10",
            numero_rps=1,
            serie_rps="1",
            prestador_cnpj="123",
            inscricao_municipal="1",
        )
        self.assertFalse(ok)
        client.consultar_nfse_por_rps.assert_called_once()
        self.assertEqual(ERR_NFSE_CONSULTA, "Falha ao consultar a NFS-e no portal")
