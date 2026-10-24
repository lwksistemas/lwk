"""Marca d\'água (logo transparente) nos PDFs assinados."""
from io import BytesIO

from PIL import Image as PILImage

from .formatters import baixar_logo_pdf
from reportlab.lib.units import cm
from reportlab.platypus import Flowable, Table


def _build_watermark_callback(logo_url, assinatura_vendedor, assinatura_cliente):
    """Prepara dados da marca d\'água (logo transparente) para uso nas assinaturas."""
    if not (assinatura_vendedor or assinatura_cliente) or not logo_url:
        return None
    try:
        conteudo = baixar_logo_pdf(logo_url)
        if not conteudo:
            return None
        pil_img = PILImage.open(BytesIO(conteudo)).convert("RGBA")
        alpha = pil_img.split()[3]
        alpha = alpha.point(lambda p: int(p * 0.25))
        pil_img.putalpha(alpha)
        out_buf = BytesIO()
        pil_img.save(out_buf, format="PNG")
        return out_buf.getvalue()
    except Exception:
        return None


def _recortar_marca(wm_bytes: bytes) -> bytes:
    """Tira a margem vazia para a logo ocupar o quadro da assinatura."""
    try:
        imagem = PILImage.open(BytesIO(wm_bytes)).convert("RGBA")
        caixa = imagem.getchannel("A").point(lambda alpha: 255 if alpha > 8 else 0).getbbox()
        if not caixa:
            return wm_bytes
        recorte = imagem.crop(caixa)
        saida = BytesIO()
        recorte.save(saida, format="PNG")
        return saida.getvalue()
    except Exception:
        return wm_bytes


class _QuadroComMarca(Flowable):
    """Desenha a logo em cada metade do quadro, cobrindo o retângulo inteiro."""

    def __init__(self, tabela, wm_bytes):
        Flowable.__init__(self)
        self.tabela = tabela
        self.wm_bytes = _recortar_marca(wm_bytes)

    def wrap(self, aw, ah):
        largura, altura = self.tabela.wrap(aw, ah)
        self.width = largura
        self.height = altura
        return largura, altura

    def draw(self):
        self._desenhar_marca()
        self.tabela.drawOn(self.canv, 0, 0)

    def _desenhar_marca(self):
        try:
            from reportlab.lib.utils import ImageReader
            imagem = ImageReader(BytesIO(self.wm_bytes))
            largura_imagem, altura_imagem = imagem.getSize()
            if not largura_imagem or not altura_imagem or self.width <= 0 or self.height <= 0:
                return
            coluna = self.width / 2
            for origem in (0, coluna):
                self.canv.saveState()
                recorte = self.canv.beginPath()
                recorte.rect(origem, 0, coluna, self.height)
                self.canv.clipPath(recorte, stroke=0, fill=0)
                escala = max(coluna / float(largura_imagem), self.height / float(altura_imagem))
                desenho_w = largura_imagem * escala
                desenho_h = altura_imagem * escala
                x = origem + (coluna - desenho_w) / 2
                y = (self.height - desenho_h) / 2 - 24
                self.canv.drawImage(
                    imagem, x, y, width=desenho_w, height=desenho_h, mask="auto", preserveAspectRatio=True,
                )
                self.canv.restoreState()
        except Exception:
            return


def _inserir_watermark_flowable(elements, wm_data, *, cell_width_cm=8, max_wm_w_cm=7.5, max_wm_h_cm=5, y_factor=0.8, preencher_quadro=False):
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
    if insert_idx is None:
        return
    if preencher_quadro:
        elements[insert_idx] = _QuadroComMarca(elements[insert_idx], wm_data)
        return
    elements.insert(insert_idx, WatermarkFlowable(wm_data))
