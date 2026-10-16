"""A emissão avisa quando o certificado A1 já venceu."""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from nfse_integration.issnet_nacional_client import ISSNetNacionalClient


class CertificadoVencidoTest(SimpleTestCase):
    def _cliente(self) -> ISSNetNacionalClient:
        return ISSNetNacionalClient(cert_bytes=b"pfx", cert_password="x")

    def test_avisa_com_a_data_de_vencimento(self):
        cert = MagicMock()
        cert.not_valid_after_utc = datetime(2026, 10, 16, 12, 16, tzinfo=timezone.utc)
        with patch(
            "nfse_integration.nacional.xml_signer.carregar_certificado_bytes",
            return_value=(None, cert, None),
        ):
            with patch(
                "django.utils.timezone.now",
                return_value=datetime(2026, 10, 16, 17, 32, tzinfo=timezone.utc),
            ):
                mensagem = self._cliente()._mensagem_certificado_vencido()
        self.assertEqual(
            mensagem,
            "O certificado digital A1 venceu em 16/10/2026 às 09:16. "
            "Renove o certificado na configuração de NFS-e antes de emitir.",
        )

    def test_certificado_valido_nao_avisa(self):
        cert = MagicMock()
        cert.not_valid_after_utc = datetime(2027, 1, 1, tzinfo=timezone.utc)
        with patch(
            "nfse_integration.nacional.xml_signer.carregar_certificado_bytes",
            return_value=(None, cert, None),
        ):
            with patch(
                "django.utils.timezone.now",
                return_value=datetime(2026, 10, 16, 17, 32, tzinfo=timezone.utc),
            ):
                self.assertIsNone(self._cliente()._mensagem_certificado_vencido())

    def test_emissao_para_antes_de_chamar_o_portal(self):
        cliente = self._cliente()
        with patch.object(
            cliente,
            "_mensagem_certificado_vencido",
            return_value="O certificado digital A1 venceu em 16/10/2026 às 09:16. "
            "Renove o certificado na configuração de NFS-e antes de emitir.",
        ):
            with patch.object(cliente, "_enviar_soap") as enviar:
                resultado = cliente.emitir_nfse(numero_lote=1, numero_dps=188)
        enviar.assert_not_called()
        self.assertFalse(resultado["success"])
        self.assertIn("venceu em 16/10/2026", resultado["erro"])
