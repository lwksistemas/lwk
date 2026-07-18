"""Carrega logo por URL como flowable ReportLab."""
import logging
from io import BytesIO

import requests
from reportlab.lib.units import cm
from reportlab.platypus import Image

logger = logging.getLogger(__name__)


def logo_image(logo_url: str, max_w=5 * cm, max_h=2.5 * cm):
    """Carrega logo por URL e retorna flowable ReportLab (proporcional)."""
    try:
        resp = requests.get(logo_url, timeout=8)
        if resp.status_code != 200:
            return None
        buf = BytesIO(resp.content)
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
