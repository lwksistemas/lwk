"""Testes de helpers do relatório de comissão e pagamento."""
from datetime import date
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from crm_vendas.relatorio_comissao_data import fmt_cpf_cnpj, resolver_periodo_relatorio
from crm_vendas.relatorio_comissao_pagamento import processar_pagamento_comissao
from crm_vendas.services_relatorio_comissao import nome_arquivo_pdf_comissao


class FmtCpfCnpjTest(SimpleTestCase):
    def test_cpf(self):
        self.assertEqual(fmt_cpf_cnpj('12345678901'), '123.456.789-01')

    def test_cnpj(self):
        self.assertEqual(fmt_cpf_cnpj('12345678000190'), '12.345.678/0001-90')

    def test_ja_formatado_retorna_original_se_tamanho_invalido(self):
        self.assertEqual(fmt_cpf_cnpj('abc'), 'abc')


class ResolverPeriodoRelatorioTest(SimpleTestCase):
    def test_periodo_customizado_iso(self):
        inicio, fim, desc, err = resolver_periodo_relatorio(
            'mes_atual',
            data_inicio_str='2026-06-01',
            data_fim_str='2026-06-30',
        )
        self.assertIsNone(err)
        self.assertEqual(inicio, date(2026, 6, 1))
        self.assertEqual(fim, date(2026, 6, 30))
        self.assertIn('01/06/2026', desc)

    def test_datas_invalidas(self):
        inicio, fim, desc, err = resolver_periodo_relatorio(
            'mes_atual',
            data_inicio_str='data-ruim',
            data_fim_str='2026-06-30',
        )
        self.assertIsNotNone(err)
        self.assertIsNone(inicio)

    @patch('crm_vendas.relatorios.calcular_periodo', return_value=(date(2026, 7, 1), date(2026, 7, 31)))
    def test_periodo_preset(self, _calc):
        inicio, fim, desc, err = resolver_periodo_relatorio('mes_atual')
        self.assertIsNone(err)
        self.assertEqual(inicio, date(2026, 7, 1))
        self.assertEqual(desc, 'Mes Atual')


class NomeArquivoPdfComissaoTest(SimpleTestCase):
    def test_nome_contem_partes_sanitizadas(self):
        nome = nome_arquivo_pdf_comissao('Empresa X', 'João Silva', 'RC-2026-07')
        self.assertIn('comissao_', nome)
        self.assertIn('RC-2026-07', nome)
        self.assertTrue(nome.endswith('.pdf'))


class ProcessarPagamentoComissaoTest(SimpleTestCase):
    @patch('crm_vendas.relatorio_comissao_pagamento.emitir_nfse_comissao_sync')
    @patch('nfse_integration.queue_dispatch.should_enqueue_nfse', return_value=False)
    def test_marca_pago_e_emite_nfse_sync(self, _enqueue, mock_emitir):
        rel = MagicMock()
        rel.id = 12
        rel.loja_id = 4
        rel.numero = 'RC-001'
        processar_pagamento_comissao(rel)
        self.assertEqual(rel.status, 'pago')
        rel.save.assert_called()
        mock_emitir.assert_called_once_with(12, 4)

    @patch('nfse_integration.queue_dispatch.enqueue_emitir_nfse_comissao')
    @patch('nfse_integration.queue_dispatch.should_enqueue_nfse', return_value=True)
    def test_marca_pago_e_enfileira_nfse(self, _enqueue_flag, mock_enqueue):
        rel = MagicMock()
        rel.id = 8
        rel.loja_id = 2
        rel.numero = 'RC-002'
        processar_pagamento_comissao(rel)
        self.assertEqual(rel.status, 'pago')
        mock_enqueue.assert_called_once_with(8, 2)
