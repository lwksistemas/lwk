"""Cliente ISSNet a partir da CRMConfig da loja (certificado em arquivo temporario)."""
import os
import tempfile
from contextlib import contextmanager
from typing import Any, Generator


def certificado_configurado_loja(config: Any) -> bool:
    return bool(
        getattr(config, 'issnet_certificado', None)
        or getattr(config, 'nacional_certificado', None)
    )


def senha_certificado_configurada_loja(config: Any) -> bool:
    return bool(
        getattr(config, 'issnet_senha_certificado', '')
        or getattr(config, 'nacional_senha_certificado', '')
    )


def ambiente_issnet_loja(config: Any) -> str:
    return (
        'homologacao'
        if getattr(config, 'issnet_ambiente_homologacao', False)
        else 'producao'
    )


@contextmanager
def issnet_client_loja(
    config: Any, *, prefix: str = 'issnet_'
) -> Generator[Any, None, None]:
    """Abre ISSNetClient com PFX temporario da configuracao CRM da loja."""
    from nfse_integration.issnet_client import ISSNetClient

    cert_data = (
        getattr(config, 'issnet_certificado', None)
        or getattr(config, 'nacional_certificado', None)
    )
    if not cert_data:
        raise ValueError('Certificado digital não configurado')

    senha_cert = (
        getattr(config, 'issnet_senha_certificado', '')
        or getattr(config, 'nacional_senha_certificado', '')
        or ''
    )
    cert_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pfx', prefix=prefix)
    try:
        cert_tmp.write(bytes(cert_data))
        cert_tmp.close()
        client = ISSNetClient(
            usuario=getattr(config, 'issnet_usuario', '') or '',
            senha=getattr(config, 'issnet_senha', '') or '',
            certificado_path=cert_tmp.name,
            senha_certificado=senha_cert,
            ambiente=ambiente_issnet_loja(config),
        )
        yield client
    finally:
        if os.path.isfile(cert_tmp.name):
            try:
                os.unlink(cert_tmp.name)
            except OSError:
                pass
