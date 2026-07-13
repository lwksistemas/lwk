"""Garante que o upload preset unsigned aceite pastas dinâmicas do cliente."""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

DEFAULT_PRESET = os.environ.get("CLOUDINARY_UPLOAD_PRESET", "lwk_padrao")


def server_image_upload_options(folder: str) -> dict:
    """Upload autenticado no modo de pastas dinâmicas do Cloudinary."""
    return {
        "asset_folder": folder,
        "use_asset_folder_as_public_id_prefix": True,
        "resource_type": "image",
    }


def _configure_cloudinary_sdk() -> bool:
    import cloudinary

    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", "").strip()
    api_key = os.environ.get("CLOUDINARY_API_KEY", "").strip()
    api_secret = os.environ.get("CLOUDINARY_API_SECRET", "").strip()

    if not cloud_name or not api_key or not api_secret:
        try:
            from superadmin.cloudinary_models import CloudinaryConfig

            cfg = CloudinaryConfig.get_config()
            if cfg.enabled and cfg.cloud_name and cfg.api_key and cfg.api_secret:
                cloud_name = cfg.cloud_name
                api_key = cfg.api_key
                api_secret = cfg.api_secret
        except Exception as exc:
            logger.debug("CloudinaryConfig indisponível: %s", exc)

    if not cloud_name or not api_key or not api_secret:
        return False

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True,
    )
    return True


def ensure_cloudinary_upload_preset(preset_name: str = DEFAULT_PRESET) -> bool:
    """Remove asset_folder fixo do preset para o widget enviar subpastas (ex.: lwksistemas/felix/login).
    """
    try:
        import cloudinary.api

        if not _configure_cloudinary_sdk():
            logger.warning("Cloudinary não configurado; preset não atualizado")
            return False

        desired = {
            "overwrite": False,
            "use_filename": False,
            "unique_filename": True,
            "use_filename_as_display_name": True,
            "use_asset_folder_as_public_id_prefix": True,
            "type": "upload",
        }

        current = cloudinary.api.upload_preset(preset_name)
        settings = current.get("settings") or {}
        if settings.get("asset_folder"):
            logger.info("Removendo asset_folder fixo do preset %s", preset_name)

        if settings == desired and not settings.get("asset_folder"):
            logger.debug("Preset %s já está correto", preset_name)
            return True

        cloudinary.api.update_upload_preset(preset_name, unsigned=True, settings=desired)
        logger.info("Preset Cloudinary %s atualizado para pastas dinâmicas", preset_name)
        return True
    except Exception as exc:
        logger.warning("Não foi possível atualizar preset Cloudinary %s: %s", preset_name, exc)
        return False
