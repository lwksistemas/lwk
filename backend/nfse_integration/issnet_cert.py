"""Carregamento de certificado A1 (.pfx) para ISSNet."""
import os
import tempfile
from contextlib import contextmanager
from typing import Generator, Tuple

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes


def carregar_certificado(pfx_path: str, senha: str):
    """Carrega chave privada e certificado de um arquivo .pfx."""
    from cryptography.hazmat.primitives.serialization import pkcs12

    with open(pfx_path, 'rb') as f:
        pfx_data = f.read()
    private_key, certificate, extra = pkcs12.load_key_and_certificates(
        pfx_data, senha.encode()
    )
    if certificate is None:
        raise ValueError('O arquivo .pfx nao contem certificado valido.')
    return private_key, certificate, extra


def materializar_pem_mtls(
    pfx_path: str, senha: str
) -> Tuple[str, str, PrivateKeyTypes, x509.Certificate]:
    """
    Grava chave e cadeia em arquivos PEM temporários para mTLS (requests/zeep).
    Retorna (key_path, cert_path, private_key, certificate).
    """
    from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat

    private_key_obj, cert_obj, extra = carregar_certificado(pfx_path, senha)
    key_pem = private_key_obj.private_bytes(
        Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()
    )
    cert_pem = cert_obj.public_bytes(Encoding.PEM)
    if extra:
        for add in extra:
            if add is not None:
                cert_pem += add.public_bytes(Encoding.PEM)

    ktf = tempfile.NamedTemporaryFile(delete=False, suffix='.pem')
    ctf = tempfile.NamedTemporaryFile(delete=False, suffix='.pem')
    try:
        ktf.write(key_pem)
        ctf.write(cert_pem)
        ktf.flush()
        ctf.flush()
        return ktf.name, ctf.name, private_key_obj, cert_obj
    finally:
        ktf.close()
        ctf.close()


@contextmanager
def certificado_mtls_temporario(
    pfx_path: str, senha: str
) -> Generator[Tuple[str, str], None, None]:
    """Context manager: paths PEM para mTLS; remove arquivos ao sair."""
    key_path, cert_path, _key, _cert = materializar_pem_mtls(pfx_path, senha)
    try:
        yield cert_path, key_path
    finally:
        for p in (cert_path, key_path):
            if p and os.path.isfile(p):
                try:
                    os.unlink(p)
                except OSError:
                    pass
