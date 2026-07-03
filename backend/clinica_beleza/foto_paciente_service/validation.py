import logging
import os

from core.cloudinary_folders import loja_clinica_fotos, loja_clinica_fotos_paths

from .constants import CLOUDINARY_HOST
from .exceptions import FotoCloudinaryInvalida

logger = logging.getLogger(__name__)


def cloudinary_upload_config(loja, ambiente: str | None = None) -> dict:
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", "dzrdbw74w")
    upload_preset = os.environ.get("CLOUDINARY_UPLOAD_PRESET", "lwk_padrao")
    try:
        from superadmin.cloudinary_models import CloudinaryConfig

        cfg = CloudinaryConfig.objects.using("default").first()
        if cfg and cfg.cloud_name:
            cloud_name = cfg.cloud_name
    except Exception as e:
        logger.debug("CloudinaryConfig: %s", e)

    folder = loja_clinica_fotos(loja, ambiente=ambiente)
    return {
        "cloud_name": cloud_name,
        "upload_preset": upload_preset,
        "folder": folder,
    }


def validar_cloudinary_foto_loja(loja, cloudinary_url: str, public_id: str = "") -> None:
    """Garante que a imagem pertence à pasta da loja no Cloudinary."""
    url = (cloudinary_url or "").strip()
    if not url.startswith("https://"):
        raise FotoCloudinaryInvalida("URL da imagem inválida.")

    cfg = cloudinary_upload_config(loja)
    cloud_name = (cfg.get("cloud_name") or "").strip()
    pastas = loja_clinica_fotos_paths(loja)
    if not cloud_name or not pastas:
        raise FotoCloudinaryInvalida("Configuração de upload indisponível.")

    expected_host = f"https://{CLOUDINARY_HOST}/{cloud_name}/"
    if not url.lower().startswith(expected_host.lower()):
        raise FotoCloudinaryInvalida("Imagem deve estar no Cloudinary desta clínica.")

    pid = (public_id or "").strip().lower()
    url_lower = url.lower()

    for folder in pastas:
        folder_prefix = f"{folder}/"
        folder_path = f"/{folder}/"
        if pid and (pid == folder or pid.startswith(folder_prefix)):
            return
        if folder_path in url_lower:
            return

    raise FotoCloudinaryInvalida("Imagem fora da pasta autorizada desta clínica.")
