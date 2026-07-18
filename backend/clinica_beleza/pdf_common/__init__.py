"""Helpers compartilhados de geração de PDF (timbrado, logo)."""

from .logo import logo_image
from .timbrado import merge_timbrado_fundo

__all__ = [
    "logo_image",
    "merge_timbrado_fundo",
]
