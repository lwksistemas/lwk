"""Factory compartilhado para ISSNetClient (loja CRM e superadmin)."""
import os
import tempfile
from collections.abc import Generator
from contextlib import contextmanager, suppress
from typing import Any


@contextmanager
def issnet_client_from_pfx(
    *,
    cert_data: bytes,
    senha_certificado: str,
    usuario: str,
    senha: str,
    ambiente: str,
    prefix: str = 'issnet_',
) -> Generator[Any, None, None]:
    """Abre ISSNetClient com certificado PFX em arquivo temporário."""
    from nfse_integration.issnet_client import ISSNetClient

    if not cert_data:
        raise ValueError('Certificado digital não configurado')

    cert_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pfx', prefix=prefix)  # noqa: SIM115
    try:
        cert_tmp.write(bytes(cert_data))
        cert_tmp.close()
        client = ISSNetClient(
            usuario=usuario or '',
            senha=senha or '',
            certificado_path=cert_tmp.name,
            senha_certificado=senha_certificado or '',
            ambiente=ambiente or 'producao',
        )
        yield client
    finally:
        if os.path.isfile(cert_tmp.name):
            with suppress(OSError):
                os.unlink(cert_tmp.name)


def _cert_bytes(config: Any) -> bytes:
    for attr in ('issnet_certificado', 'nacional_certificado'):
        raw = getattr(config, attr, None)
        if not raw:
            continue
        try:
            data = bytes(raw)
        except Exception:
            continue
        if len(data) > 0:
            return data
    return b''


def certificado_configurado(config: Any) -> bool:
    """True somente quando há conteúdo binário do certificado (não só nome do arquivo)."""
    return len(_cert_bytes(config)) > 0


def _senha_cert(config: Any) -> str:
    return (
        getattr(config, 'issnet_senha_certificado', '')
        or getattr(config, 'nacional_senha_certificado', '')
        or ''
    )


@contextmanager
def issnet_client_loja(config: Any, *, prefix: str = 'issnet_') -> Generator[Any, None, None]:
    """ISSNetClient a partir da CRMConfig da loja."""
    ambiente = (
        'homologacao'
        if getattr(config, 'issnet_ambiente_homologacao', False)
        else 'producao'
    )
    with issnet_client_from_pfx(
        cert_data=_cert_bytes(config),
        senha_certificado=_senha_cert(config),
        usuario=getattr(config, 'issnet_usuario', '') or '',
        senha=getattr(config, 'issnet_senha', '') or '',
        ambiente=ambiente,
        prefix=prefix,
    ) as client:
        yield client


@contextmanager
def issnet_client_superadmin(config: Any, *, prefix: str = 'issnet_') -> Generator[Any, None, None]:
    """ISSNetClient a partir da SuperadminNFSeConfig."""
    from core.encryption import decrypt_value

    with issnet_client_from_pfx(
        cert_data=_cert_bytes(config),
        senha_certificado=decrypt_value(_senha_cert(config)),
        usuario=decrypt_value(getattr(config, 'issnet_usuario', '') or ''),
        senha=decrypt_value(getattr(config, 'issnet_senha', '') or ''),
        ambiente=getattr(config, 'nacional_ambiente', None) or 'producao',
        prefix=prefix,
    ) as client:
        yield client
