"""Helpers ISSNet no contexto da loja (CRM). Cliente em issnet_client_factory."""
from nfse_integration.issnet_client_factory import (
    certificado_configurado,
    issnet_client_loja,
)

__all__ = ["certificado_configurado_loja", "issnet_client_loja", "senha_certificado_configurada_loja"]


def certificado_configurado_loja(config) -> bool:
    return certificado_configurado(config)


def senha_certificado_configurada_loja(config) -> bool:
    return bool(
        getattr(config, "issnet_senha_certificado", "")
        or getattr(config, "nacional_senha_certificado", ""),
    )
