"""
Views — assinatura digital do termo de consentimento.

Re-exporta módulos internos e públicos para compatibilidade com urls.py.
"""
from .views_assinatura_consentimento_internas import (
    ConsultaDownloadTermoPdfView,
    ConsultaEnviarTermoAssinaturaView,
    ConsultaReenviarTermoAssinaturaView,
    ConsultaTermoConsentimentoStatusView,
)
from .views_assinatura_consentimento_publicas import (
    ConsultaAssinaturaPdfPublicaView,
    ConsultaAssinaturaPublicaView,
)

__all__ = [
    'ConsultaAssinaturaPdfPublicaView',
    'ConsultaAssinaturaPublicaView',
    'ConsultaDownloadTermoPdfView',
    'ConsultaEnviarTermoAssinaturaView',
    'ConsultaReenviarTermoAssinaturaView',
    'ConsultaTermoConsentimentoStatusView',
]
