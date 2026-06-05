"""Testes unitários do relatório de comissões (funções puras)."""
from decimal import Decimal
from unittest import TestCase
from unittest.mock import MagicMock

from clinica_beleza.comissao_relatorio_service import (
    _alocar_valores_pagamento,
    _calcular_comissao_regra,
    _formatar_regra,
    _procedimentos_vinculados_consulta,
    _resolver_regra_consulta,
)


def _comissao(modo: str, valor: str):
    c = MagicMock()
    c.modo = modo
    c.valor = Decimal(valor)
    return c


class ComissaoRelatorioHelpersTest(TestCase):
    def test_formatar_regra_percentual(self):
        modo, regra = _formatar_regra(_comissao('percentual', '25'))
        self.assertEqual(modo, 'percentual')
        self.assertEqual(regra, '25%')

    def test_formatar_regra_fixo(self):
        modo, regra = _formatar_regra(_comissao('fixo', '85'))
        self.assertEqual(modo, 'fixo')
        self.assertEqual(regra, 'R$ 85,00')

    def test_resolver_regra_consulta_prioriza_local(self):
        regra_local = _comissao('fixo', '200')
        regra_geral = _comissao('percentual', '35')
        regras = {
            'consulta': regra_geral,
            'consultas_local': {10: regra_local},
            'procedimentos': {},
        }
        self.assertIs(_resolver_regra_consulta(regras, 10), regra_local)
        self.assertIsNone(_resolver_regra_consulta(regras, 99))
        self.assertIsNone(_resolver_regra_consulta(regras, None))

    def test_comissao_fixo_independe_da_base(self):
        val = _calcular_comissao_regra(_comissao('fixo', '100'), Decimal('0'))
        self.assertEqual(val, Decimal('100'))

    def test_alocar_valores_multiplos_procedimentos(self):
        procs = [
            {'procedure_id': 1, 'procedimento_nome': 'A', 'valor': Decimal('900')},
            {'procedure_id': 2, 'procedimento_nome': 'B', 'valor': Decimal('1924')},
        ]
        vc, vp_map = _alocar_valores_pagamento(Decimal('2924'), Decimal('100'), procs)
        self.assertEqual(vc, Decimal('100'))
        self.assertEqual(vp_map[1], Decimal('900'))
        self.assertEqual(vp_map[2], Decimal('1924'))
        self.assertEqual(vc + vp_map[1] + vp_map[2], Decimal('2924'))

    def test_procedimentos_vinculados_via_appointment_procedure(self):
        appt = MagicMock()
        ap1 = MagicMock(
            procedure_id=1,
            valor=Decimal('900'),
            procedure=MagicMock(nome='Imunidade', preco=Decimal('800')),
        )
        ap2 = MagicMock(
            procedure_id=2,
            valor=Decimal('1924'),
            procedure=MagicMock(nome='Massagem', preco=Decimal('1500')),
        )
        appt.appointment_procedures.select_related.return_value.order_by.return_value = [
            ap1, ap2,
        ]
        consulta = MagicMock(procedure_id=None, procedure=None)
        items = _procedimentos_vinculados_consulta(appt, consulta)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['procedimento_nome'], 'Imunidade')
