"""Carrega logo por URL como flowable ReportLab."""
import logging
from io import BytesIO

import requests
from reportlab.lib.units import cm
from reportlab.platypus import Image

logger = logging.getLogger(__name__)


def logo_url_permitida(logo_url: str) -> bool:
    """Só baixa logo do servidor de mídia da loja (anti-SSRF)."""
    from core.media_storage import is_media_url

    return is_media_url((logo_url or "").strip())


def baixar_logo(logo_url: str, *, timeout: int = 5) -> bytes | None:
    """Baixa a logo se a URL for da mídia. Sem redirect."""
    if not logo_url_permitida(logo_url):
        logger.warning("Logo recusada (URL fora da mídia)")
        return None
    try:
        resp = requests.get(logo_url, timeout=timeout, allow_redirects=False)
        if resp.status_code != 200 or not resp.content:
            return None
        return resp.content
    except Exception as exc:
        logger.warning("Falha ao baixar logo: %s", exc)
        return None


def logo_image(logo_url: str, max_w=5 * cm, max_h=2.5 * cm):
    """Carrega logo por URL e retorna flowable ReportLab (proporcional)."""
    try:
        conteudo = baixar_logo(logo_url, timeout=8)
        if not conteudo:
            return None
        buf = BytesIO(conteudo)
        from PIL import Image as PILImage

        pil = PILImage.open(buf)
        iw, ih = pil.size
        aspect = ih / float(iw)
        width = min(max_w, iw)
        height = width * aspect
        if height > max_h:
            height = max_h
            width = height / aspect
        buf.seek(0)
        img = Image(buf, width=width, height=height)
        img.hAlign = "CENTER"
        return img
    except Exception as e:
        logger.warning("Falha ao carregar logo para PDF: %s", e)
        return None
