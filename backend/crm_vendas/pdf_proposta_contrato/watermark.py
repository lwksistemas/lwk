"""Marca d\'água (logo transparente) nos PDFs assinados."""
from io import BytesIO

import requests
from PIL import Image as PILImage
from reportlab.lib.units import cm
from reportlab.platypus import Flowable, Table


def _build_watermark_callback(logo_url, assinatura_vendedor, assinatura_cliente):
    """Prepara dados da marca d\'água (logo transparente) para uso nas assinaturas."""
    if not (assinatura_vendedor or assinatura_cliente) or not logo_url:
        return None
    try:
        resp = requests.get(logo_url, timeout=5)
        if resp.status_code != 200:
            return None
        pil_img = PILImage.open(BytesIO(resp.content)).convert("RGBA")
        alpha = pil_img.split()[3]
        alpha = alpha.point(lambda p: int(p * 0.25))
        pil_img.putalpha(alpha)
        out_buf = BytesIO()
        pil_img.save(out_buf, format="PNG")
        return out_buf.getvalue()
    except Exception:
        return None


def _inserir_watermark_flowable(elements, wm_data, *, cell_width_cm=8, max_wm_w_cm=7.5, max_wm_h_cm=5, y_factor=0.8):
    """Insere flowable de marca d\'água antes da última tabela (assinaturas)."""
    if not wm_data:
        return

    class WatermarkFlowable(Flowable):
        def __init__(self, wm_bytes):
            Flowable.__init__(self)
            self.wm_bytes = wm_bytes
            self.width = 16 * cm
            self.height = 0

        def draw(self):
            try:
                from reportlab.lib.utils import ImageReader
                img = ImageReader(BytesIO(self.wm_bytes))
                iw, ih = img.getSize()
                wm_w = max_wm_w_cm * cm
                wm_h = wm_w * (ih / float(iw))
                if wm_h > max_wm_h_cm * cm:
                    wm_h = max_wm_h_cm * cm
                    wm_w = wm_h / (ih / float(iw))
                y_offset = -(wm_h * y_factor)
                cell_w = cell_width_cm * cm
                x_left = (cell_w - wm_w) / 2
                x_right = cell_w + (cell_w - wm_w) / 2
                self.canv.drawImage(img, x_left, y_offset, width=wm_w, height=wm_h, mask="auto", preserveAspectRatio=True)
                self.canv.drawImage(img, x_right, y_offset, width=wm_w, height=wm_h, mask="auto", preserveAspectRatio=True)
            except Exception:
                pass

    insert_idx = None
    for i in range(len(elements) - 1, -1, -1):
        if isinstance(elements[i], Table):
            insert_idx = i
            break
    if insert_idx is not None:
        elements.insert(insert_idx, WatermarkFlowable(wm_data))
