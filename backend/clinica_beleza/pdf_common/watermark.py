"""Logo semitransparente para marca d'água em caixas do PDF (pedido/orçamento)."""
from io import BytesIO

from PIL import Image as PILImage
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Flowable, Table

from .logo import baixar_logo

WM_OPACIDADE = 0.50


def watermark_logo_bytes(logo_url: str, opacidade: float | None = None) -> bytes | None:
    if not logo_url:
        return None
    fator = WM_OPACIDADE if opacidade is None else opacidade
    try:
        conteudo = baixar_logo(logo_url, timeout=5)
        if not conteudo:
            return None
        pil_img = PILImage.open(BytesIO(conteudo)).convert("RGBA")
        alpha = pil_img.split()[3]
        alpha = alpha.point(lambda p: int(p * fator))
        pil_img.putalpha(alpha)
        out = BytesIO()
        pil_img.save(out, format="PNG")
        return out.getvalue()
    except Exception:
        return None


class MarcaDaguaColunas(Flowable):
    """Marca d'água repetida em duas colunas (ex.: atrás das assinaturas do termo).

    Flowable de altura 0: desenha a logo nas colunas esquerda e direita, abaixo
    da linha-base, com offset vertical configurável. Deve ser inserido logo antes
    da tabela de duas colunas que ele decora.
    """

    def __init__(
        self,
        wm_bytes: bytes | None,
        *,
        largura=16 * cm,
        max_w=6.6 * cm,
        max_h=3.6 * cm,
        y_factor: float = 1.12,
        descer=0.48 * cm,
    ):
        Flowable.__init__(self)
        self.wm_bytes = wm_bytes
        self.width = largura
        self.height = 0
        self._max_w = max_w
        self._max_h = max_h
        self._y_factor = y_factor
        self._descer = descer

    def draw(self):
        if not self.wm_bytes:
            return
        try:
            img = ImageReader(BytesIO(self.wm_bytes))
            iw, ih = img.getSize()
            if not (iw and ih):
                return
            wm_w = self._max_w
            wm_h = wm_w * (ih / float(iw))
            if wm_h > self._max_h:
                wm_h = self._max_h
                wm_w = wm_h / (ih / float(iw))
            y_offset = -(wm_h * self._y_factor) - self._descer
            metade = self.width / 2
            x_left = (metade - wm_w) / 2
            x_right = metade + (metade - wm_w) / 2
            for x in (x_left, x_right):
                self.canv.drawImage(
                    img, x, y_offset, width=wm_w, height=wm_h,
                    mask="auto", preserveAspectRatio=True,
                )
        except Exception:
            pass


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
