"""Re-exports de helpers de timbrado/logo (compatibilidade)."""
from ..pdf_common import logo_image as _logo_image
from ..pdf_common import merge_timbrado_fundo as _merge_timbrado_fundo

__all__ = ["_logo_image", "_merge_timbrado_fundo"]
