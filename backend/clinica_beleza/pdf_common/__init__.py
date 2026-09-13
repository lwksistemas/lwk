"""Helpers compartilhados de geração de PDF (timbrado, logo)."""

from .finalize import finalize_pdf_com_timbrado
from .logo import logo_image
from .timbrado import merge_timbrado_fundo
from .watermark import QuadroComMarcaDagua, watermark_logo_bytes

__all__ = [
    "QuadroComMarcaDagua",
    "finalize_pdf_com_timbrado",
    "logo_image",
    "merge_timbrado_fundo",
    "watermark_logo_bytes",
]
