"""Tamanho e intensidade da logo no quadro da assinatura digital."""
from django.test import SimpleTestCase

from crm_vendas.pdf_proposta_contrato.watermark import (
    escala_logo_no_quadro,
    normalizar_logo_assinatura,
)


class LogoAssinaturaTest(SimpleTestCase):
    def test_padrao_cobre_o_quadro_com_intensidade_atual(self):
        self.assertEqual(normalizar_logo_assinatura(None, None), (100, 25))
        self.assertEqual(normalizar_logo_assinatura(100, 25), (100, 25))

    def test_valor_fora_da_faixa_volta_ao_padrao(self):
        self.assertEqual(normalizar_logo_assinatura(10, 99), (100, 25))

    def test_tamanho_menor_reduz_a_logo_dentro_do_quadro(self):
        cheia = escala_logo_no_quadro(200, 100, 400, 200, 100)
        metade = escala_logo_no_quadro(200, 100, 400, 200, 50)
        self.assertEqual(cheia, 2)
        self.assertEqual(metade, 1)
