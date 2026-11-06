"""Número curto da NFS-e para tela, PDF e e-mail.

A chave de acesso nacional tem 50 dígitos e não cabe como número da nota.
O número legível vem da tag nNFSe do XML autorizado.
"""
from __future__ import annotations

from typing import Any

PORTAL_CONSULTA_NACIONAL = "https://www.nfse.gov.br/ConsultaPublica/?tpc=1&chave={chave}"


def eh_chave_acesso_nacional(valor: str | None) -> bool:
    texto = (valor or "").strip()
    return len(texto) >= 44 and texto.isdigit()


def chave_acesso_nfse(nf: Any) -> str:
    for campo in ("codigo_verificacao", "numero_nf"):
        valor = (getattr(nf, campo, None) or "").strip()
        if eh_chave_acesso_nacional(valor):
            return valor
    return ""


def numero_nfse_para_exibicao(nf: Any) -> str:
    """Número da NFS-e para o usuário. Na nota nacional, o nNFSe do XML."""
    if (getattr(nf, "provedor", "") or "").strip().lower() == "nacional":
        from nfse_integration.issnet_nacional_xml_builder import extrair_numero_nfse_nacional

        extraido = extrair_numero_nfse_nacional(getattr(nf, "xml_nfse", "") or "")
        if extraido and extraido.isdigit():
            return str(int(extraido))
    numero = (getattr(nf, "numero_nf", None) or "").strip()
    if numero.isdigit() and len(numero) <= 15:
        return str(int(numero))
    return numero
