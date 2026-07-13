"""Testes do PDF de comissões (merge timbrado)."""
import unittest
from io import BytesIO

try:
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas

    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False


def _pdf_com_texto(texto: str, paginas: int = 1) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf)
    for i in range(paginas):
        c.drawString(72, 750, f"{texto}-{i + 1}")
        c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()


class CodigoPagamentoPdfTest(unittest.TestCase):
    def setUp(self):
        from clinica_beleza.comissao_relatorio_pdf import _codigo_pagamento_pdf
        self.cod = _codigo_pagamento_pdf

    def test_pix(self):
        self.assertEqual(self.cod("PIX"), "PIX")

    def test_credito(self):
        self.assertEqual(self.cod("Cartão de crédito"), "CC")

    def test_debito(self):
        self.assertEqual(self.cod("Cartão de débito"), "CD")

    def test_pagamento_misto(self):
        self.assertEqual(
            self.cod("Cartão de débito + Cartão de crédito"),
            "CD+CC",
        )


class FmtRegraComissaoTest(unittest.TestCase):
    def setUp(self):
        from clinica_beleza.comissao_relatorio_pdf import _fmt_regra_comissao
        self.fmt = _fmt_regra_comissao

    def test_percentual(self):
        self.assertEqual(self.fmt("percentual", "30,00%"), "30,00% (%)")

    def test_fixo(self):
        self.assertEqual(self.fmt("fixo", "R$ 188,00"), "R$ 188,00 (fixo)")

    def test_vazio(self):
        self.assertEqual(self.fmt("", ""), "—")


@unittest.skipUnless(HAS_DEPS, "pypdf/reportlab não instalados")
class MergeTimbradoPdfTest(unittest.TestCase):
    def setUp(self):
        from clinica_beleza.comissao_relatorio_pdf import _merge_timbrado_fundo
        self.merge = _merge_timbrado_fundo

    def test_uma_pagina_conteudo_gera_uma_saida(self):
        timbrado = _pdf_com_texto("FUNDO", 1)
        conteudo = _pdf_com_texto("UNICA", 1)
        merged = self.merge(conteudo, timbrado)
        reader = PdfReader(BytesIO(merged))
        self.assertEqual(len(reader.pages), 1)

    def test_duas_paginas_conteudo_nao_repetem_primeira(self):
        timbrado = _pdf_com_texto("FUNDO", 1)
        conteudo_buf = BytesIO()
        w = PdfWriter()
        for label in ("PAGINA_A", "PAGINA_B"):
            p = PdfReader(BytesIO(_pdf_com_texto(label, 1))).pages[0]
            w.add_page(p)
        w.write(conteudo_buf)
        conteudo = conteudo_buf.getvalue()

        merged = self.merge(conteudo, timbrado)
        reader = PdfReader(BytesIO(merged))
        self.assertEqual(len(reader.pages), 2)
        textos = [reader.pages[i].extract_text() or "" for i in range(2)]
        self.assertIn("PAGINA_A", textos[0])
        self.assertIn("PAGINA_B", textos[1])
        self.assertNotIn("PAGINA_B", textos[0])


if __name__ == "__main__":
    unittest.main()
