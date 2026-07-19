"""Linhas de taxa/desconto no recibo com retorno gratuito e prazo."""
from unittest import SimpleTestCase
from unittest.mock import MagicMock, patch

from clinica_beleza.recibo.context import (
    _linhas_descontos_recibo,
    _linhas_taxa_consulta_recibo,
)
from clinica_beleza.recibo.retorno_info import montar_info_retorno_recibo


class LinhasTaxaConsultaReciboTests(SimpleTestCase):
    def test_retorno_gratuito_mostra_apenas_taxa_de_tabela(self):
        linhas = _linhas_taxa_consulta_recibo(
            {
                "retorno_gratuito": True,
                "taxa_consulta": 0.0,
                "taxa_consulta_referencia": 300.0,
                "retorno_dias": 30,
            },
        )
        self.assertEqual(linhas, [("Taxa de consulta", 300.0)])

    def test_desconto_retorno_com_prazo(self):
        linhas = _linhas_descontos_recibo(
            {
                "retorno_gratuito": True,
                "taxa_consulta_referencia": 300.0,
                "desconto_retorno": 300.0,
                "desconto": 0.0,
                "retorno_dias": 30,
            },
        )
        self.assertEqual(
            linhas,
            [("Desconto retorno (prazo 30 dias)", 300.0)],
        )

    def test_desconto_retorno_e_comercial(self):
        linhas = _linhas_descontos_recibo(
            {
                "retorno_gratuito": True,
                "desconto_retorno": 300.0,
                "desconto": 50.0,
                "retorno_dias": None,
            },
        )
        self.assertEqual(
            linhas,
            [
                ("Desconto retorno", 300.0),
                ("Desconto", 50.0),
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


class MontarInfoRetornoReciboTests(SimpleTestCase):
    @patch("clinica_beleza.retorno_service.get_agenda_retorno_config")
    def test_aviso_quando_retorno_aplicado_por_consulta(self, mock_config):
        cfg = MagicMock(
            retorno_procedimento_ativo=False,
            retorno_consulta_ativo=True,
            dias_retorno_consulta=30,
        )
        mock_config.return_value = cfg
        consulta = MagicMock(
            loja_id=1,
            retorno_gratuito=True,
            retorno_tipo="consulta",
            valor_consulta=0,
            local_atendimento=MagicMock(valor_consulta=180),
            appointment=None,
        )
        info = montar_info_retorno_recibo(consulta, loja_id=1)
        self.assertTrue(info["retorno_gratuito"])
        self.assertEqual(info["taxa_consulta_referencia"], 180.0)
        self.assertEqual(info["retorno_dias"], 30)
        self.assertIn("30", info["retorno_aviso"])
        self.assertIn("isenta", info["retorno_aviso"].lower())

    @patch("clinica_beleza.models.RetornoProcedimentoRegra.objects")
    @patch("clinica_beleza.retorno_service.get_agenda_retorno_config")
    def test_aviso_politica_em_atendimento_pago(self, mock_config, mock_regras):
        cfg = MagicMock(
            retorno_procedimento_ativo=False,
            retorno_consulta_ativo=True,
            dias_retorno_consulta=20,
        )
        mock_config.return_value = cfg
        mock_regras.filter.return_value.select_related.return_value = []
        consulta = MagicMock(
            loja_id=1,
            retorno_gratuito=False,
            retorno_tipo="",
            valor_consulta=150,
            local_atendimento=MagicMock(valor_consulta=150),
            appointment=None,
            procedure_id=None,
        )
        info = montar_info_retorno_recibo(consulta, loja_id=1)
        self.assertFalse(info["retorno_gratuito"])
        self.assertEqual(info["retorno_dias"], 20)
        self.assertIn("20", info["retorno_aviso"])
        self.assertIn("Retorno gratuito", info["retorno_aviso"])
