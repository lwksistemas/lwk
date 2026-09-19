"""Testes do recurso de prazo de pagamento / inadimplência / cobrança.

Foco na lógica pura (SimpleTestCase + MagicMock), sem tocar o banco.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

from django.test import SimpleTestCase

from clinica_beleza.cobranca_service import (
    MENSAGEM_COBRANCA_PADRAO,
    montar_mensagem_cobranca,
)
from clinica_beleza.models.patients import Patient
from clinica_beleza.prazo_service import (
    PrazoNaoConfiguradoError,
    calcular_vencimento,
)


class CalcularVencimentoTest(SimpleTestCase):
    def test_dias_apos_soma_dias(self):
        p = Patient(prazo_pagamento_modo="DIAS_APOS", prazo_pagamento_dias=10)
        self.assertEqual(calcular_vencimento(p, date(2026, 10, 5)), date(2026, 10, 15))

    def test_dia_fixo_vai_para_mes_seguinte_quando_finaliza_antes(self):
        p = Patient(prazo_pagamento_modo="DIA_FIXO", prazo_pagamento_dia_mes=10)
        self.assertEqual(calcular_vencimento(p, date(2026, 10, 5)), date(2026, 11, 10))

    def test_dia_fixo_vai_para_mes_seguinte_quando_finaliza_depois(self):
        p = Patient(prazo_pagamento_modo="DIA_FIXO", prazo_pagamento_dia_mes=10)
        self.assertEqual(calcular_vencimento(p, date(2026, 10, 15)), date(2026, 11, 10))

    def test_dia_fixo_vira_o_ano_em_dezembro(self):
        p = Patient(prazo_pagamento_modo="DIA_FIXO", prazo_pagamento_dia_mes=10)
        self.assertEqual(calcular_vencimento(p, date(2026, 12, 20)), date(2027, 1, 10))

    def test_sem_politica_bloqueia(self):
        p = Patient(prazo_pagamento_modo="")
        with self.assertRaises(PrazoNaoConfiguradoError):
            calcular_vencimento(p, date(2026, 10, 5))

    def test_dias_apos_sem_dias_bloqueia(self):
        p = Patient(prazo_pagamento_modo="DIAS_APOS", prazo_pagamento_dias=None)
        with self.assertRaises(PrazoNaoConfiguradoError):
            calcular_vencimento(p, date(2026, 10, 5))


class TemPrazoPagamentoTest(SimpleTestCase):
    def test_dias_apos_valido(self):
        self.assertTrue(Patient(prazo_pagamento_modo="DIAS_APOS", prazo_pagamento_dias=10).tem_prazo_pagamento)

    def test_dia_fixo_valido(self):
        self.assertTrue(Patient(prazo_pagamento_modo="DIA_FIXO", prazo_pagamento_dia_mes=10).tem_prazo_pagamento)

    def test_sem_modo_falso(self):
        self.assertFalse(Patient(prazo_pagamento_modo="").tem_prazo_pagamento)

    def test_dia_fixo_sem_dia_falso(self):
        self.assertFalse(Patient(prazo_pagamento_modo="DIA_FIXO", prazo_pagamento_dia_mes=None).tem_prazo_pagamento)


class PaymentVencidoTest(SimpleTestCase):
    """Properties esta_vencido / dias_atraso / em_aberto do Payment."""

    def _payment(self, **kwargs):
        from clinica_beleza.models.financeiro import Payment

        defaults = dict(id=1, status="PENDING", amount=Decimal(0), valor_total=Decimal(1000))
        defaults.update(kwargs)
        p = Payment(**defaults)
        # Simula prefetch da lista do Financeiro (sem parcelas) para evitar query real.
        p._prefetched_objects_cache = {"parcelas": []}
        return p

    def test_vencido_quando_venc_no_passado_e_em_aberto(self):
        ontem = date.today() - timedelta(days=3)
        p = self._payment(status="PENDING", data_vencimento=ontem)
        self.assertTrue(p.esta_vencido)
        self.assertEqual(p.dias_atraso, 3)

    def test_nao_vencido_sem_data(self):
        p = self._payment(status="PENDING", data_vencimento=None)
        self.assertFalse(p.esta_vencido)
        self.assertEqual(p.dias_atraso, 0)

    def test_nao_vencido_com_venc_futuro(self):
        amanha = date.today() + timedelta(days=5)
        p = self._payment(status="PENDING", data_vencimento=amanha)
        self.assertFalse(p.esta_vencido)

    def test_pago_nao_esta_vencido(self):
        ontem = date.today() - timedelta(days=3)
        p = self._payment(status="PAID", amount=Decimal(1000), data_vencimento=ontem)
        self.assertFalse(p.esta_vencido)


class MensagemCobrancaTest(SimpleTestCase):
    def _ctx(self):
        return {
            "nome": "Ana",
            "valor": "600,00",
            "vencimento": "10/11/2026",
            "dias_atraso": 5,
            "clinica": "Clínica X",
        }

    def test_usa_padrao_quando_config_vazia(self):
        config = MagicMock(mensagem_cobranca="")
        msg = montar_mensagem_cobranca(config, self._ctx())
        self.assertIn("Ana", msg)
        self.assertIn("600,00", msg)

    def test_usa_template_da_loja(self):
        config = MagicMock(mensagem_cobranca="Oi {nome}, deve R$ {valor}.")
        msg = montar_mensagem_cobranca(config, self._ctx())
        self.assertEqual(msg, "Oi Ana, deve R$ 600,00.")

    def test_placeholder_invalido_cai_no_padrao(self):
        config = MagicMock(mensagem_cobranca="Oi {campo_que_nao_existe}")
        msg = montar_mensagem_cobranca(config, self._ctx())
        self.assertEqual(msg, MENSAGEM_COBRANCA_PADRAO.format(**self._ctx()))
