import io
import logging

from .constants import (
    JPEG_QUALIDADE_INICIAL,
    JPEG_QUALIDADE_MINIMA,
    JPEG_QUALIDADE_PASSO,
    LIMITE_UPLOAD_BYTES,
    MAX_LADO_IMAGEM,
    MIN_LADO_IMAGEM,
)
from .exceptions import FotoUploadInvalida

logger = logging.getLogger(__name__)


def _parece_imagem_bytes(conteudo: bytes) -> bool:
    return (
        len(conteudo) >= 4
        and (
            conteudo[:3] == b"\xff\xd8\xff"
            or conteudo[:8] == b"\x89PNG\r\n\x1a\n"
            or (len(conteudo) > 12 and conteudo[:4] == b"RIFF" and conteudo[8:12] == b"WEBP")
        )
    )


def _extrair_arquivo_multipart_bruto(body: bytes, content_type: str) -> bytes | None:
    """Fallback quando o Django não populou request.FILES (ex.: proxy ou iOS)."""
    import re

    match = re.search(r"boundary=([^;\s]+)", content_type or "", re.IGNORECASE)
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


def comprimir_imagem_bytes(conteudo: bytes) -> bytes:
    """Reduz JPEG/PNG/HEIC do celular (alvo ~1,5 MB, qualidade moderada para estética)."""
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
    while max_lado >= MIN_LADO_IMAGEM:
        copia = img.copy()
        w, h = copia.size
        maior = max(w, h)
        if maior > max_lado:
            escala = max_lado / maior
            copia = copia.resize(
                (max(1, int(w * escala)), max(1, int(h * escala))),
                Image.Resampling.LANCZOS,
            )

        qualidade = JPEG_QUALIDADE_INICIAL
        while qualidade >= JPEG_QUALIDADE_MINIMA:
            buf = io.BytesIO()
            copia.save(buf, format="JPEG", quality=qualidade, optimize=True)
            dados = buf.getvalue()
            if len(dados) <= LIMITE_UPLOAD_BYTES:
                return dados
            qualidade -= JPEG_QUALIDADE_PASSO
        max_lado = int(max_lado * 0.9)

    # Última tentativa: piso de qualidade um pouco abaixo só se ainda > alvo.
    buf = io.BytesIO()
    w, h = img.size
    maior = max(w, h)
    if maior > MIN_LADO_IMAGEM:
        escala = MIN_LADO_IMAGEM / maior
        img = img.resize(
            (max(1, int(w * escala)), max(1, int(h * escala))),
            Image.Resampling.LANCZOS,
        )
    img.save(buf, format="JPEG", quality=JPEG_QUALIDADE_MINIMA, optimize=True)
    dados = buf.getvalue()
    if len(dados) <= LIMITE_UPLOAD_BYTES * 2:
        return dados

    raise FotoUploadInvalida(
        "Não foi possível reduzir a imagem. Tente outra foto ou menor resolução.",
    )


def upload_foto_media(loja, conteudo: bytes, ambiente: str | None = None, patient=None) -> dict:
    """Comprime e envia a foto ao servidor de mídia (pasta por paciente quando houver)."""
    del ambiente  # mantido na assinatura por compatibilidade com chamadas antigas
    from urllib.parse import urlparse

    from core.media_storage import media_upload, pasta_media_paciente

    comprimido = comprimir_imagem_bytes(conteudo)
    folder = "fotos"
    if patient is not None:
        folder = f"fotos/{pasta_media_paciente(patient)}"
    url = media_upload(loja, comprimido, filename="foto.jpg", folder=folder)
    if not url:
        raise FotoUploadInvalida("Falha ao enviar imagem. Tente novamente.")
    path = urlparse(url).path.lstrip("/")
    return {"secure_url": url, "public_id": path}


def _parse_media_path(url: str) -> tuple[str, str] | None:
    """Extrai (folder, filename) de URL pública validada do media server."""
    from core.media_storage import parse_media_url

    parsed = parse_media_url(url)
    if not parsed:
        return None
    _tenant, folder, filename = parsed
    return folder, filename


def excluir_foto_media(loja, foto_url: str, public_id: str = "") -> bool:
    """Remove imagem do servidor de mídia (fail-closed se URL inválida)."""
    from core.media_storage import media_delete

    from .exceptions import FotoUrlInvalida
    from .validation import validar_foto_loja

    url = (foto_url or "").strip()
    pid = (public_id or "").strip()
    if not url:
        return False

    try:
        validar_foto_loja(loja, url, pid)
    except FotoUrlInvalida:
        logger.warning(
            "Tentativa de excluir foto fora da pasta da loja %s: %s",
            getattr(loja, "slug", loja.id),
            url or pid,
        )
        return False

    parsed = _parse_media_path(url)
    if not parsed:
        logger.warning("URL de mídia sem path reconhecível: %s", url)
        return False
    folder, filename = parsed
    ok = media_delete(loja, filename, folder=folder)
    if ok:
        logger.info("Foto removida do servidor de mídia: %s/%s", folder, filename)
    return ok
