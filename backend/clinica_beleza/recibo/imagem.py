"""Converte o PDF do recibo em JPEG (foto no WhatsApp e no e-mail)."""
from __future__ import annotations

import io
import logging

logger = logging.getLogger(__name__)


def pdf_para_jpeg(pdf_bytes: bytes, *, scale: float = 2.0, quality: int = 85) -> bytes:
    """Rasteriza todas as páginas do PDF em um JPEG (páginas empilhadas)."""
    if not pdf_bytes or not pdf_bytes.startswith(b"%PDF"):
        raise ValueError("PDF inválido para converter em imagem.")

    import pypdfium2 as pdfium
    from PIL import Image

    documento = pdfium.PdfDocument(pdf_bytes)
    paginas: list[Image.Image] = []
    try:
        if len(documento) == 0:
            raise ValueError("PDF sem páginas.")
        for indice in range(len(documento)):
            pagina = documento[indice]
            try:
                bitmap = pagina.render(scale=scale)
                paginas.append(bitmap.to_pil())
            finally:
                pagina.close()
    finally:
        documento.close()

    if len(paginas) == 1:
        imagem = paginas[0]
    else:
        largura = max(p.width for p in paginas)
        altura = sum(p.height for p in paginas)
        imagem = Image.new("RGB", (largura, altura), "white")
        y = 0
        for pagina_img in paginas:
            if pagina_img.mode != "RGB":
                pagina_img = pagina_img.convert("RGB")
            imagem.paste(pagina_img, (0, y))
            y += pagina_img.height

    if imagem.mode != "RGB":
        imagem = imagem.convert("RGB")
    buffer = io.BytesIO()
    imagem.save(buffer, format="JPEG", quality=quality, optimize=True)
    jpeg = buffer.getvalue()
    if not jpeg:
        raise ValueError("Falha ao gerar JPEG do recibo.")
    return jpeg
