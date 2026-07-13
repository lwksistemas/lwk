"""Validação de certificado NFS-e (conteúdo binário, não só nome)."""
from unittest.mock import MagicMock

from django.test import SimpleTestCase

from nfse_integration.issnet_client_factory import certificado_configurado


class CertificadoConfiguradoTests(SimpleTestCase):
    def test_vazio_sem_bytes(self):
        cfg = MagicMock()
        cfg.issnet_certificado = None
        cfg.nacional_certificado = None
        self.assertFalse(certificado_configurado(cfg))

    def test_nome_sem_conteudo_nao_conta(self):
        cfg = MagicMock()
        cfg.issnet_certificado = b""
        cfg.nacional_certificado = None
        self.assertFalse(certificado_configurado(cfg))

    def test_com_pfx_valido(self):
        cfg = MagicMock()
        cfg.issnet_certificado = b"fake-pfx-bytes"
        self.assertTrue(certificado_configurado(cfg))
