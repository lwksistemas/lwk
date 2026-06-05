"""Testes do PDF de comissões (merge timbrado)."""
from io import BytesIO
import unittest

try:
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas

    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

from clinica_beleza.comissao_relatorio_pdf import _merge_timbrado_fundo


def _pdf_com_texto(texto: str, paginas: int = 1) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf)
    for i in range(paginas):
        c.drawString(72, 750, f'{texto}-{i + 1}')
        c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()


@unittest.skipUnless(HAS_DEPS, 'pypdf/reportlab não instalados')
class MergeTimbradoPdfTest(unittest.TestCase):
    def test_duas_paginas_conteudo_nao_repetem_primeira(self):
        timbrado = _pdf_com_texto('FUNDO', 1)
        conteudo_buf = BytesIO()
        w = PdfWriter()
        for label in ('PAGINA_A', 'PAGINA_B'):
            p = PdfReader(BytesIO(_pdf_com_texto(label, 1))).pages[0]
            w.add_page(p)
        w.write(conteudo_buf)
        conteudo = conteudo_buf.getvalue()

        merged = _merge_timbrado_fundo(conteudo, timbrado)
        reader = PdfReader(BytesIO(merged))
        self.assertEqual(len(reader.pages), 2)
        textos = [reader.pages[i].extract_text() or '' for i in range(2)]
        self.assertIn('PAGINA_A', textos[0])
        self.assertIn('PAGINA_B', textos[1])
        self.assertNotIn('PAGINA_B', textos[0])


if __name__ == '__main__':
    unittest.main()
