"""Linhas de taxa/desconto no recibo com retorno gratuito e prazo."""
from unittest.mock import MagicMock, patch

from django.test import TestCase

from clinica_beleza.recibo.context import (
    _linhas_descontos_recibo,
    _linhas_taxa_consulta_recibo,
    aplicar_valor_consulta_do_local,
)
from clinica_beleza.recibo.retorno_info import montar_info_retorno_recibo


class LinhasTaxaConsultaReciboTests(TestCase):
    def test_retorno_gratuito_nao_imprime_a_taxa(self):
        linhas = _linhas_taxa_consulta_recibo(
            {
                "retorno_gratuito": True,
                "taxa_consulta": 0.0,
                "taxa_consulta_referencia": 300.0,
                "retorno_dias": 30,
            },
        )
        self.assertEqual(linhas, [])

    def test_opcao_desligada_nao_injeta_taxa_com_procedimento(self):
        ctx = aplicar_valor_consulta_do_local(
            {
                "retorno_gratuito": False,
                "cobrar_taxa_com_procedimento": False,
                "taxa_consulta": 0.0,
                "taxa_consulta_referencia": 150.0,
                "procedimentos": [{"nome": "BOTOX", "valor": 1500.0}],
                "subtotal": 1500.0,
                "valor_total": 1500.0,
                "valor_pago": 1500.0,
                "saldo_devedor": 0.0,
            },
        )
        self.assertEqual(ctx["taxa_consulta"], 0.0)
        self.assertEqual(ctx["subtotal"], 1500.0)
        self.assertEqual(_linhas_taxa_consulta_recibo(ctx), [])

    def test_opcao_desligada_consulta_sem_procedimento_mantem_taxa(self):
        ctx = aplicar_valor_consulta_do_local(
            {
                "retorno_gratuito": False,
                "cobrar_taxa_com_procedimento": False,
                "taxa_consulta": 0.0,
                "taxa_consulta_referencia": 150.0,
                "procedimentos": [{"nome": "Consulta", "valor": 0.0}],
                "subtotal": 0.0,
                "valor_total": 0.0,
                "valor_pago": 0.0,
                "saldo_devedor": 0.0,
            },
        )
        self.assertEqual(ctx["taxa_consulta"], 150.0)
        self.assertEqual(ctx["valor_total"], 150.0)

    def test_sem_retorno_com_procedimento_usa_taxa_do_local(self):
        ctx = aplicar_valor_consulta_do_local(
            {
                "retorno_gratuito": False,
                "taxa_consulta": 0.0,
                "taxa_consulta_referencia": 150.0,
                "procedimentos": [{"nome": "TIRZEPATIDA 2,5 MG", "valor": 150.0}],
                "subtotal": 150.0,
                "valor_total": 150.0,
                "valor_pago": 150.0,
                "saldo_devedor": 0.0,
            },
        )
        self.assertEqual(ctx["taxa_consulta"], 150.0)
        self.assertEqual(ctx["subtotal"], 300.0)
        self.assertEqual(
            _linhas_taxa_consulta_recibo(ctx),
            [("Taxa de consulta", 150.0)],
        )

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
            [("Desconto retorno", 300.0)],
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


class MontarInfoRetornoReciboTests(TestCase):
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
        self.assertIn("foi integralmente descontada neste atendimento", info["retorno_aviso"])
        self.assertIn("após o atendimento", info["retorno_aviso"])
        self.assertIn("R$ 180,00", info["retorno_aviso"])
        self.assertNotIn("configurado", info["retorno_aviso"])

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
        self.assertIn("dá direito a retorno gratuito", info["retorno_aviso"])
        self.assertNotIn("após este atendimento", info["retorno_aviso"])
        self.assertNotIn("configurado", info["retorno_aviso"])
        self.assertNotIn("dia(s)", info["retorno_aviso"])
