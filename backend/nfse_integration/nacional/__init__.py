"""Provedor NFS-e Nacional (ADN - Ambiente de Dados Nacional).

Emissão de NFS-e via DPS (Declaração de Prestação de Serviço) no padrão nacional.
Fluxo: XML DPS → Assinatura XMLDSIG → GZip → Base64 → POST /DFe (mTLS)
"""
from .client import NacionalClient

__all__ = ["NacionalClient"]
