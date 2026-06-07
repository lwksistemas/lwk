"""Queryset do relatório de comissão — vendas sem empresa prestadora."""
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from crm_vendas.models import Conta, Lead, Oportunidade
from crm_vendas.services_relatorio_comissao import queryset_oportunidades_comissao


class RelatorioComissaoQuerysetTest(TestCase):
    loja_id = 1

    def setUp(self):
        self.ep = Conta.objects.create(
            loja_id=self.loja_id,
            nome='Empresa A',
            tipo='empresa_prestadora',
            cnpj='12345678000199',
        )
        self.lead = Lead.objects.create(
            loja_id=self.loja_id,
            nome='Cliente Teste',
            cpf_cnpj='12345678901',
        )
        self.inicio = date(2026, 6, 1)
        self.fim = date(2026, 6, 30)

    def _criar_venda(self, *, empresa_prestadora=None, titulo='Venda'):
        return Oportunidade.objects.create(
            loja_id=self.loja_id,
            titulo=titulo,
            lead=self.lead,
            valor=Decimal('1000.00'),
            valor_comissao=Decimal('100.00'),
            etapa='closed_won',
            empresa_prestadora=empresa_prestadora,
            data_fechamento_ganho=date(2026, 6, 5),
        )

    def test_inclui_venda_sem_empresa_prestadora(self):
        self._criar_venda(empresa_prestadora=self.ep, titulo='Com EP')
        self._criar_venda(empresa_prestadora=None, titulo='Sem EP')

        qs = queryset_oportunidades_comissao(
            self.loja_id,
            self.ep.id,
            None,
            self.inicio,
            self.fim,
        )
        self.assertEqual(qs.count(), 2)

    def test_exclui_venda_de_outra_empresa_prestadora(self):
        outra = Conta.objects.create(
            loja_id=self.loja_id,
            nome='Empresa B',
            tipo='empresa_prestadora',
            cnpj='98765432000188',
        )
        self._criar_venda(empresa_prestadora=self.ep)
        self._criar_venda(empresa_prestadora=outra, titulo='Outra EP')

        qs = queryset_oportunidades_comissao(
            self.loja_id,
            self.ep.id,
            None,
            self.inicio,
            self.fim,
        )
        self.assertEqual(qs.count(), 1)
