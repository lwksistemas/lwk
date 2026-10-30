"""O .pfx só é gravado se o PKCS#12 abrir, e a emissão lê o blob cifrado."""
from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import BestAvailableEncryption, pkcs12
from cryptography.x509.oid import NameOID
from django.test import SimpleTestCase

from core.encryption import PFX_PREFIX
from nfse_integration.certificado_armazenado import (
    CertificadoInvalido,
    ler_pfx,
    preparar_pfx_para_gravar,
)
from nfse_integration.nacional.xml_signer import carregar_certificado_bytes


def _pfx(senha: bytes) -> bytes:
    chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nome = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "lwk-teste")])
    agora = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(nome)
        .issuer_name(nome)
        .public_key(chave.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(agora)
        .not_valid_after(agora + timedelta(days=2))
        .sign(chave, hashes.SHA256())
    )
    return pkcs12.serialize_key_and_certificates(
        name=b"lwk-teste",
        key=chave,
        cert=cert,
        cas=None,
        encryption_algorithm=BestAvailableEncryption(senha),
    )


class CertificadoCifradoTest(SimpleTestCase):
    def test_upload_valido_grava_cifrado_e_a_emissao_abre(self):
        original = _pfx(b"senha-a1")
        gravado = preparar_pfx_para_gravar(original, "senha-a1")
        self.assertTrue(gravado.startswith(PFX_PREFIX))
        self.assertNotIn(original, gravado)
        chave, cert, _extra = carregar_certificado_bytes(gravado, "senha-a1")
        self.assertIsNotNone(chave)
        self.assertIsNotNone(cert)

    def test_senha_errada_nao_grava(self):
        original = _pfx(b"senha-a1")
        with self.assertRaises(CertificadoInvalido):
            preparar_pfx_para_gravar(original, "outra")

    def test_pfx_antigo_em_claro_continua_abrindo(self):
        original = _pfx(b"senha-a1")
        self.assertEqual(ler_pfx(original), original)
        chave, cert, _extra = carregar_certificado_bytes(original, "senha-a1")
        self.assertIsNotNone(chave)
        self.assertIsNotNone(cert)
