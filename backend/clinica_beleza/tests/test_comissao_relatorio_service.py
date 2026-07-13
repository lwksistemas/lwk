"""Testes unitários do relatório de comissões (funções puras)."""
from decimal import Decimal
from unittest import TestCase
from unittest.mock import MagicMock, patch

from clinica_beleza.comissao_relatorio_service import (
    _agrupar_pagamentos_por_agendamento,
    _alocar_valores_pagamento,
    _calcular_comissao_regra,
    _combinar_formas_pagamento,
    _formatar_regra,
    _procedimentos_vinculados_consulta,
    _resolver_local_atendimento_efetivo,
    _resolver_regra_consulta,
    _resolver_regra_procedimento,
    _resolver_valor_consulta_cadastro,
    calcular_comissao_payment_atendimento,
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
        self.assertIs(_resolver_regra_consulta(regras, 99), regra_geral)
        self.assertIs(_resolver_regra_consulta(regras, None), regra_geral)

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

    def test_resolver_local_prioriza_vinculo_na_consulta(self):
        consulta = MagicMock(local_atendimento_id=3)
        consulta.local_atendimento = MagicMock(nome='Consultório Principal')
        regras = {'consultas_local': {1: _comissao('fixo', '300'), 2: _comissao('percentual', '30')}}
        local_id, nome = _resolver_local_atendimento_efetivo(consulta, regras, Decimal('800'))
        self.assertEqual(local_id, 3)
        self.assertEqual(nome, 'Consultório Principal')

    def test_resolver_valor_consulta_usa_local_quando_cadastro_zerado(self):
        consulta = MagicMock(valor_consulta=Decimal('0'))
        consulta.local_atendimento = MagicMock(valor_consulta=Decimal('800'))
        procs = [{'procedure_id': 1, 'procedimento_nome': 'Radio', 'valor': Decimal('276')}]
        vc = _resolver_valor_consulta_cadastro(consulta, Decimal('1076'), procs)
        self.assertEqual(vc, Decimal('800'))

    def test_resolver_valor_consulta_infere_restante_do_pagamento(self):
        consulta = MagicMock(valor_consulta=Decimal('0'), local_atendimento=None)
        procs = [{'procedure_id': 1, 'procedimento_nome': 'Radio', 'valor': Decimal('276')}]
        vc = _resolver_valor_consulta_cadastro(consulta, Decimal('1076'), procs)
        self.assertEqual(vc, Decimal('800'))

    def test_resolver_valor_consulta_reserva_taxa_local_com_multiplos_procedimentos(self):
        consulta = MagicMock(valor_consulta=Decimal('0'), local_atendimento=None, local_atendimento_id=None)
        regras = {
            'consulta': None,
            'consultas_local': {3: _comissao('percentual', '30')},
            'procedimentos': {},
        }
        procs = [
            {'procedure_id': 1, 'procedimento_nome': 'Botox', 'valor': Decimal('800')},
            {'procedure_id': 2, 'procedimento_nome': 'Radiofrequência', 'valor': Decimal('276')},
        ]
        with self.subTest('sem regra não reserva taxa'):
            self.assertEqual(
                _resolver_valor_consulta_cadastro(consulta, Decimal('1076'), procs),
                Decimal('0'),
            )
        with self.subTest('com regra e local vinculado usa taxa do local'):
            consulta_local = MagicMock(
                valor_consulta=Decimal('0'),
                local_atendimento_id=3,
                local_atendimento=MagicMock(valor_consulta=Decimal('300')),
            )
            taxa = _resolver_valor_consulta_cadastro(consulta_local, Decimal('1076'), procs, regras)
            self.assertEqual(taxa, Decimal('300'))

    def test_alocar_prioriza_taxa_consulta_e_mantem_procedimento_com_regra(self):
        procs = [
            {'procedure_id': 1, 'procedimento_nome': 'Botox', 'valor': Decimal('800')},
            {'procedure_id': 2, 'procedimento_nome': 'Radiofrequência', 'valor': Decimal('276')},
        ]
        vc, vp_map = _alocar_valores_pagamento(
            Decimal('1076'), Decimal('300'), procs, proc_ids_com_regra={2},
        )
        self.assertEqual(vc, Decimal('300'))
        self.assertEqual(vp_map[2], Decimal('276'))
        self.assertEqual(vp_map[1], Decimal('500'))
        self.assertEqual(vc + vp_map[1] + vp_map[2], Decimal('1076'))

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

    def test_combinar_formas_pagamento_unica(self):
        p = MagicMock(payment_method='DEBIT_CARD')
        self.assertEqual(_combinar_formas_pagamento([p]), 'Cartão de débito')

    def test_combinar_formas_pagamento_mista(self):
        p1 = MagicMock(payment_method='DEBIT_CARD')
        p2 = MagicMock(payment_method='CREDIT_CARD')
        self.assertEqual(
            _combinar_formas_pagamento([p1, p2]),
            'Cartão de débito + Cartão de crédito',
        )

    def test_agrupar_pagamentos_por_agendamento_soma_valores(self):
        appt = MagicMock(id=42, professional=MagicMock())
        p1 = MagicMock(appointment=appt, appointment_id=42, amount=Decimal('300'))
        p2 = MagicMock(appointment=appt, appointment_id=42, amount=Decimal('300'))
        p3 = MagicMock(appointment=MagicMock(id=99), appointment_id=99, amount=Decimal('100'))
        grupos = _agrupar_pagamentos_por_agendamento([p1, p2, p3])
        self.assertEqual(len(grupos), 2)
        self.assertEqual(grupos[0]['total_amount'], Decimal('600'))
        self.assertEqual(len(grupos[0]['payments']), 2)

    def test_resolver_regra_procedimento_prioriza_convenio(self):
        regra_unimed = _comissao('fixo', '300')
        regra_geral = _comissao('percentual', '25')
        proc_map = {
            (10, 1): regra_unimed,
            (10, None): regra_geral,
        }
        self.assertIs(_resolver_regra_procedimento(proc_map, 10, 1), regra_unimed)
        self.assertIs(_resolver_regra_procedimento(proc_map, 10, 2), regra_geral)

    @patch('clinica_beleza.comissao_relatorio.atendimento._calcular_comissao_regra', return_value=Decimal('45'))
    @patch('clinica_beleza.comissao_relatorio.atendimento._resolver_regra_consulta')
    @patch(
        'clinica_beleza.comissao_relatorio.atendimento._resolver_local_atendimento_efetivo',
        return_value=(1, 'Consultório'),
    )
    @patch(
        'clinica_beleza.comissao_relatorio.atendimento._alocar_valores_pagamento',
        return_value=(Decimal('150'), {}),
    )
    @patch(
        'clinica_beleza.comissao_relatorio.atendimento._resolver_valor_consulta_cadastro',
        return_value=Decimal('150'),
    )
    @patch('clinica_beleza.comissao_relatorio.atendimento.resolver_convenio_atendimento_comissao', return_value=None)
    @patch('clinica_beleza.comissao_relatorio.atendimento._regras_profissional')
    @patch('clinica_beleza.comissao_relatorio.atendimento._procedimentos_vinculados_consulta', return_value=[])
    def test_calcular_comissao_pagamento_somente_taxa_consulta(
        self,
        _mock_procs,
        mock_regras,
        _mock_conv,
        _mock_valor_cad,
        _mock_alocar,
        _mock_local,
        _mock_regra_consulta,
        _mock_calc_regra,
    ):
        mock_regras.return_value = {
            'consulta': _comissao('percentual', '30'),
            'consultas_local': {},
            'procedimentos': {},
            'procedimento_ids': set(),
        }
        appt = MagicMock(professional_id=1, id=1, pk=1)
        appt._prefetched_objects_cache = {'appointment_procedures': True}
        consulta = MagicMock(valor_consulta=Decimal('150'))

        pct, total = calcular_comissao_payment_atendimento(
            appointment=appt,
            consulta=consulta,
            amount=Decimal('150'),
        )
        self.assertEqual(total, Decimal('45'))
        self.assertEqual(pct, 30)
