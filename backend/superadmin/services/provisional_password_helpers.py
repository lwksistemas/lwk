"""
URLs de login para emails de senha provisória — uma única fonte (FRONTEND_URL / settings).
"""
from __future__ import annotations

from django.conf import settings


def frontend_base_url() -> str:
    return getattr(settings, 'FRONTEND_URL', 'https://lwksistemas.com.br').rstrip('/')


def loja_login_absolute_url(loja) -> str:
    """URL completa da página de login da loja (multi-tenant)."""
    return f"{frontend_base_url()}{loja.login_page_url}"


def sistema_usuario_login_url(tipo: str) -> str:
    """tipo: 'superadmin' ou 'suporte'."""
    return f"{frontend_base_url()}/{tipo}/login"
