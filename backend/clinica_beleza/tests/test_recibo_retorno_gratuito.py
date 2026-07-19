"""Linhas de taxa de consulta no recibo com retorno gratuito."""
from unittest import SimpleTestCase

from clinica_beleza.recibo.context import _linhas_taxa_consulta_recibo


class LinhasTaxaConsultaReciboTests(SimpleTestCase):
    def test_retorno_gratuito_mostra_valor_e_isencao(self):
        linhas = _linhas_taxa_consulta_recibo(
            {
                "retorno_gratuito": True,
                "taxa_consulta": 0.0,
                "taxa_consulta_referencia": 150.0,
            },
        )
        self.assertEqual(
            linhas,
            [
                ("Taxa de consulta", 150.0),
                ("Retorno gratuito", 0.0),
            ],
        )

    def test_taxa_normal_sem_retorno(self):
        linhas = _linhas_taxa_consulta_recibo(
            {"retorno_gratuito": False, "taxa_consulta": 200.0},
        )
        self.assertEqual(linhas, [("Taxa de consulta", 200.0)])

    def test_sem_taxa_e_sem_retorno(self):
        linhas = _linhas_taxa_consulta_recibo(
            {"retorno_gratuito": False, "taxa_consulta": 0.0},
        )
        self.assertEqual(linhas, [])
