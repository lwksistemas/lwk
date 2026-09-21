"""Logo semitransparente para marca d'água em caixas do PDF (pedido/orçamento)."""
from io import BytesIO

from PIL import Image as PILImage

from .logo import baixar_logo
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Flowable, Table

WM_OPACIDADE = 0.50


def watermark_logo_bytes(logo_url: str) -> bytes | None:
    if not logo_url:
        return None
    try:
        conteudo = baixar_logo(logo_url, timeout=5)
        if not conteudo:
            return None
        pil_img = PILImage.open(BytesIO(conteudo)).convert("RGBA")
        alpha = pil_img.split()[3]
        alpha = alpha.point(lambda p: int(p * WM_OPACIDADE))
        pil_img.putalpha(alpha)
        out = BytesIO()
        pil_img.save(out, format="PNG")
        return out.getvalue()
    except Exception:
        return None


class QuadroComMarcaDagua(Flowable):
    """Tabela com a logo da clínica centralizada no fundo."""

    def __init__(self, table: Table, wm_bytes: bytes | None):
        Flowable.__init__(self)
        self.table = table
        self.wm_bytes = wm_bytes
        self.width = 0
        self.height = 0

    def wrap(self, availWidth, availHeight):
        w, h = self.table.wrap(availWidth, availHeight)
        self.width = w
        self.height = h
        return w, h

    def draw(self):
        if self.wm_bytes and self.width and self.height:
            try:
                img = ImageReader(BytesIO(self.wm_bytes))
                iw, ih = img.getSize()
                if iw and ih:
                    max_w = self.width * 0.92
                    max_h = self.height * 0.88
                    wm_w = max_w
                    wm_h = wm_w * (ih / float(iw))
                    if wm_h > max_h:
                        wm_h = max_h
                        wm_w = wm_h / (ih / float(iw))
                    x = (self.width - wm_w) / 2
                    y = (self.height - wm_h) / 2
                    self.canv.drawImage(
                        img, x, y, width=wm_w, height=wm_h,
                        mask="auto", preserveAspectRatio=True,
                    )
            except Exception:
                pass
        self.table.drawOn(self.canv, 0, 0)
