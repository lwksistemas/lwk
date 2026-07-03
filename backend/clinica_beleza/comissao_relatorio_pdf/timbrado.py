import logging
from io import BytesIO

import requests
from reportlab.lib.units import cm
from reportlab.platypus import Image

logger = logging.getLogger(__name__)


def _merge_timbrado_fundo(content_pdf: bytes, timbrado_pdf: bytes) -> bytes:
    """Coloca o timbrado atrás de cada página de conteúdo (sem duplicar folhas)."""
    try:
        from pypdf import PdfReader, PdfWriter, Transformation
    except ImportError:
        logger.warning('pypdf não instalado; PDF sem fundo timbrado.')
        return content_pdf

    try:
        reader_c = PdfReader(BytesIO(content_pdf))
        if not reader_c.pages:
            return content_pdf

        reader_t = PdfReader(BytesIO(timbrado_pdf))
        if not reader_t.pages:
            return content_pdf

        writer = PdfWriter()
        writer.append(reader_c)

        for i in range(len(writer.pages)):
            timbrado = PdfReader(BytesIO(timbrado_pdf)).pages[0]
            writer.pages[i].merge_transformed_page(
                timbrado,
                Transformation(),
                over=False,
            )

        out = BytesIO()
        writer.write(out)
        out.seek(0)
        return out.getvalue()
    except Exception as e:
        logger.warning('Falha ao mesclar timbrado no PDF de comissões: %s', e)
        return content_pdf


def _logo_image(logo_url: str, max_w=5 * cm, max_h=2.5 * cm):
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
        img.hAlign = 'CENTER'
        return img
    except Exception as e:
        logger.warning('Logo no PDF de comissões: %s', e)
        return None
