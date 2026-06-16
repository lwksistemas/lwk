"""
URLs de login para emails de senha provisória — uma única fonte (FRONTEND_URL / settings).
"""
from __future__ import annotations

from django.conf import settings


def frontend_base_url() -> str:
    return getattr(settings, 'FRONTEND_URL', 'https://lwksistemas.com.br').rstrip('/')


def loja_login_absolute_url(loja) -> str:
    """
    URL completa da página de login da loja (multi-tenant).

    Usa o atalho amigável (ex: /loja/sorriso/login) em vez do slug interno
    (ex: /loja/34787081845/login) para que o link do email funcione corretamente.
    O endpoint info_publica resolve tanto slug quanto atalho, mas a URL visível
    ao cliente deve ser a amigável.
    """
    atalho_ou_slug = (getattr(loja, 'atalho', '') or '').strip() or loja.slug
    return f"{frontend_base_url()}/loja/{atalho_ou_slug}/login"


def sistema_usuario_login_url(tipo: str) -> str:
    """tipo: 'superadmin' ou 'suporte'."""
    return f"{frontend_base_url()}/{tipo}/login"
