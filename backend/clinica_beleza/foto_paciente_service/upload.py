import io
import logging
import os

from core.cloudinary_upload_preset import server_image_upload_options

from .constants import LIMITE_UPLOAD_BYTES, MAX_LADO_IMAGEM
from .exceptions import FotoUploadInvalida
from .validation import cloudinary_upload_config

logger = logging.getLogger(__name__)


def _parece_imagem_bytes(conteudo: bytes) -> bool:
    if len(conteudo) < 4:
        return False
    if conteudo[:3] == b"\xff\xd8\xff":
        return True
    if conteudo[:8] == b"\x89PNG\r\n\x1a\n":
        return True
    if len(conteudo) > 12 and conteudo[:4] == b"RIFF" and conteudo[8:12] == b"WEBP":
        return True
    return False


def _extrair_arquivo_multipart_bruto(body: bytes, content_type: str) -> bytes | None:
    """Fallback quando o Django não populou request.FILES (ex.: proxy ou iOS)."""
    import re

    match = re.search(r"boundary=([^;\s]+)", content_type or "", re.I)
    if not match or not body:
        return None
    boundary = match.group(1).strip().strip('"').encode()
    separador = b"--" + boundary
    for parte in body.split(separador):
        if b"filename=" not in parte:
            continue
        if b"\r\n\r\n" not in parte:
            continue
        _, conteudo = parte.split(b"\r\n\r\n", 1)
        conteudo = conteudo.rstrip(b"\r\n")
        if conteudo.endswith(b"--"):
            conteudo = conteudo[:-2].rstrip(b"\r\n")
        if conteudo and _parece_imagem_bytes(conteudo):
            return conteudo
    return None


def extrair_bytes_upload_request(request) -> bytes | None:
    """Lê bytes da imagem enviada pelo celular (multipart, campo file ou corpo binário)."""
    for campo in ("file", "image", "foto", "photo"):
        arquivo = request.FILES.get(campo)
        if arquivo:
            return arquivo.read()

    if request.FILES:
        arquivo = next(iter(request.FILES.values()))
        return arquivo.read()

    content_type = (getattr(request, "content_type", None) or "").lower()
    body = request.body or b""

    if body and _parece_imagem_bytes(body):
        return body

    if "multipart/form-data" in content_type and body:
        extraido = _extrair_arquivo_multipart_bruto(body, content_type)
        if extraido:
            return extraido

    return None


def parse_json_body_seguro(request) -> dict:
    """Evita UnicodeDecodeError quando o corpo é binário (multipart/imagem)."""
    import json

    body = request.body or b""
    if not body:
        return {}

    content_type = (getattr(request, "content_type", None) or "").lower()
    if "application/json" not in content_type:
        inicio = body.lstrip()[:1]
        if inicio not in (b"{", b"["):
            return {}

    try:
        texto = body.decode("utf-8")
    except UnicodeDecodeError:
        return {}

    try:
        return json.loads(texto or "{}")
    except json.JSONDecodeError:
        return {}


def _configurar_cloudinary_sdk() -> dict | None:
    """Retorna cloud_name/api_key/api_secret ou None se indisponível."""
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", "").strip()
    api_key = os.environ.get("CLOUDINARY_API_KEY", "").strip()
    api_secret = os.environ.get("CLOUDINARY_API_SECRET", "").strip()
    try:
        from superadmin.cloudinary_models import CloudinaryConfig

        cfg = CloudinaryConfig.get_config()
        if cfg.enabled and cfg.cloud_name and cfg.api_key and cfg.api_secret:
            cloud_name = cfg.cloud_name.strip()
            api_key = cfg.api_key.strip()
            api_secret = cfg.api_secret.strip()
    except Exception as exc:
        logger.debug("CloudinaryConfig: %s", exc)
    if not (cloud_name and api_key and api_secret):
        return None
    try:
        import cloudinary

        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )
    except ImportError:
        return None
    return {"cloud_name": cloud_name, "api_key": api_key, "api_secret": api_secret}


def comprimir_imagem_bytes(conteudo: bytes) -> bytes:
    """Reduz JPEG/PNG/HEIC do celular para ficar abaixo do limite do Cloudinary."""
    from PIL import Image, ImageOps

    if not conteudo:
        raise FotoUploadInvalida("Arquivo vazio.")

    try:
        img = Image.open(io.BytesIO(conteudo))
        img = ImageOps.exif_transpose(img)
    except Exception as exc:
        raise FotoUploadInvalida("Arquivo não é uma imagem válida.") from exc

    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    max_lado = MAX_LADO_IMAGEM
    while max_lado >= 960:
        copia = img.copy()
        w, h = copia.size
        maior = max(w, h)
        if maior > max_lado:
            escala = max_lado / maior
            copia = copia.resize(
                (max(1, int(w * escala)), max(1, int(h * escala))),
                Image.Resampling.LANCZOS,
            )

        qualidade = 88
        while qualidade >= 45:
            buf = io.BytesIO()
            copia.save(buf, format="JPEG", quality=qualidade, optimize=True)
            dados = buf.getvalue()
            if len(dados) <= LIMITE_UPLOAD_BYTES:
                return dados
            qualidade -= 8
        max_lado = int(max_lado * 0.75)

    raise FotoUploadInvalida(
        "Não foi possível reduzir a imagem. Tente outra foto ou menor resolução.",
    )


def upload_foto_cloudinary(loja, conteudo: bytes, ambiente: str | None = None) -> dict:
    """Envia bytes comprimidos ao Cloudinary (upload autenticado no servidor)."""
    if not _configurar_cloudinary_sdk():
        raise FotoUploadInvalida("Upload de imagem indisponível no momento.")

    import cloudinary.uploader

    cfg = cloudinary_upload_config(loja, ambiente=ambiente)
    folder = (cfg.get("folder") or "").strip()
    if not folder:
        raise FotoUploadInvalida("Pasta de upload não configurada.")

    comprimido = comprimir_imagem_bytes(conteudo)
    try:
        resultado = cloudinary.uploader.upload(
            comprimido,
            **server_image_upload_options(folder),
            overwrite=True,
        )
    except Exception as exc:
        logger.exception("Erro upload Cloudinary foto paciente")
        raise FotoUploadInvalida("Falha ao enviar imagem. Tente novamente.") from exc

    url = (resultado.get("secure_url") or "").strip()
    if not url:
        raise FotoUploadInvalida("Resposta inválida do serviço de imagens.")
    return {
        "secure_url": url,
        "public_id": (resultado.get("public_id") or "").strip(),
    }


def excluir_foto_cloudinary(loja, cloudinary_url: str, public_id: str = "") -> bool:
    """Remove imagem do Cloudinary. Retorna True se removida ou já inexistente."""
    from .exceptions import FotoCloudinaryInvalida
    from .validation import validar_cloudinary_foto_loja

    url = (cloudinary_url or "").strip()
    pid = (public_id or "").strip()
    if not url and not pid:
        return False

    try:
        validar_cloudinary_foto_loja(loja, url, pid)
    except FotoCloudinaryInvalida:
        logger.warning(
            "Tentativa de excluir foto fora da pasta da loja %s: %s",
            getattr(loja, "slug", loja.id),
            url or pid,
        )
        return False

    if not _configurar_cloudinary_sdk():
        logger.error("Cloudinary indisponível para exclusão de foto do paciente")
        return False

    from superadmin.cloudinary_utils import extract_public_id_from_url

    import cloudinary.uploader

    target_pid = pid or extract_public_id_from_url(url)
    if not target_pid:
        logger.error("Não foi possível obter public_id para exclusão: %s", url)
        return False

    try:
        result = cloudinary.uploader.destroy(target_pid)
    except Exception:
        logger.exception("Exceção ao remover foto do Cloudinary: %s", target_pid)
        return False

    if result.get("result") in ("ok", "not found"):
        logger.info("Foto removida do Cloudinary: %s", target_pid)
        return True

    logger.error("Erro ao remover foto do Cloudinary: %s", result)
    return False
