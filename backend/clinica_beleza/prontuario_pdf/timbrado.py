"""Mescla papel timbrado (PDF de fundo) ao conteúdo gerado."""
from io import BytesIO

from .constants import logger


def merge_timbrado_fundo(content_pdf: bytes, timbrado_pdf: bytes) -> bytes:
    """Coloca o timbrado atrás de cada página de conteúdo."""
    try:
        from pypdf import PdfReader, PdfWriter, Transformation
    except ImportError:
        logger.warning("pypdf não instalado; PDF sem fundo timbrado.")
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
        logger.warning("Falha ao mesclar timbrado no PDF: %s", e)
        return content_pdf
