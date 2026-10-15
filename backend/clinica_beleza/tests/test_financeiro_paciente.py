"""Testes do prazo criado pelo admin e do saldo de procedimento anterior."""
from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase

from clinica_beleza.models.patients import Patient
from clinica_beleza.prazo_service import aplicar_prazo_escolhido, validar_regra_prazo
from clinica_beleza.procedimento_anterior_service import (
    saldo_anterior,
    validar_lancamento_anterior,
    validar_recebimento,
)


class _Opcao:
    def __init__(self, pk, modo, dias=None, dia_mes=None):
        self.pk = pk
        self.modo = modo
        self.dias = dias
        self.dia_mes = dia_mes


class PrazoCriadoPeloAdminTest(SimpleTestCase):
    def test_dias_apos_guarda_so_os_dias(self):
        modo, dias, dia = validar_regra_prazo("DIAS_APOS", "10", "5")
        self.assertEqual((modo, dias, dia), ("DIAS_APOS", 10, None))

    def test_dia_fixo_guarda_so_o_dia(self):
        modo, dias, dia = validar_regra_prazo("DIA_FIXO", None, 10)
        self.assertEqual((modo, dias, dia), ("DIA_FIXO", None, 10))

    def test_semanal_nao_pede_numero(self):
        modo, dias, dia = validar_regra_prazo("SEMANAL", "7", "10")
        self.assertEqual((modo, dias, dia), ("SEMANAL", None, None))

    def test_aplicar_semanal_na_cliente(self):
        paciente = Patient()
        aplicar_prazo_escolhido(paciente, _Opcao(8, "SEMANAL"))
        self.assertEqual(paciente.prazo_pagamento_modo, "SEMANAL")
        self.assertIsNone(paciente.prazo_pagamento_dias)
        self.assertIsNone(paciente.prazo_pagamento_dia_mes)
        self.assertTrue(paciente.tem_prazo_pagamento)

    def test_dia_acima_de_28_recusa(self):
        with self.assertRaises(ValueError):
            validar_regra_prazo("DIA_FIXO", None, 31)

    def test_aplicar_copia_a_regra_para_a_cliente(self):
        paciente = Patient()
        aplicar_prazo_escolhido(paciente, _Opcao(4, "DIAS_APOS", dias=15))
        self.assertEqual(paciente.prazo_opcao_id, 4)
        self.assertEqual(paciente.prazo_pagamento_modo, "DIAS_APOS")
        self.assertEqual(paciente.prazo_pagamento_dias, 15)
        self.assertIsNone(paciente.prazo_pagamento_dia_mes)
        self.assertTrue(paciente.tem_prazo_pagamento)

    def test_sem_prazo_limpa_a_regra(self):
        paciente = Patient(prazo_pagamento_modo="DIA_FIXO", prazo_pagamento_dia_mes=10, prazo_opcao_id=2)
        aplicar_prazo_escolhido(paciente, None)
        self.assertIsNone(paciente.prazo_opcao_id)
        self.assertEqual(paciente.prazo_pagamento_modo, "")
        self.assertFalse(paciente.tem_prazo_pagamento)


class SaldoProcedimentoAnteriorTest(SimpleTestCase):
    def test_saldo_desconta_entrada_e_recebimentos(self):
        saldo = saldo_anterior(Decimal("1000.00"), Decimal("300.00"), [Decimal("200.00")])
        self.assertEqual(saldo, Decimal("500.00"))

    def test_saldo_nao_fica_negativo(self):
        self.assertEqual(saldo_anterior("100.00", "100.00", []), Decimal("0.00"))

    def test_entrada_maior_que_o_valor_recusa(self):
        with self.assertRaises(ValueError):
            validar_lancamento_anterior(date(2024, 5, 1), "Botox", "200", "250", date(2026, 10, 15))

    def test_data_futura_recusa(self):
        with self.assertRaises(ValueError):
            validar_lancamento_anterior(date(2026, 10, 20), "Botox", "200", "0", date(2026, 10, 15))

    def test_recebimento_acima_do_saldo_recusa(self):
        with self.assertRaises(ValueError):
            validar_recebimento(
                Decimal("100.00"), "150", date(2026, 10, 15), date(2026, 10, 15), date(2024, 1, 1), "PIX",
            )

    def test_recebimento_aceita_o_saldo_no_pix(self):
        valor, forma = validar_recebimento(
            Decimal("80.00"), "80", date(2026, 10, 15), date(2026, 10, 15), date(2024, 1, 1), "PIX",
        )
        self.assertEqual(valor, Decimal("80.00"))
        self.assertEqual(forma, "PIX")

    def test_diferenca_vence_no_prazo_da_cliente(self):
        paciente = Patient(prazo_pagamento_modo="DIAS_APOS", prazo_pagamento_dias=10)
        nome, valor, pago, data_pago, vencimento = validar_lancamento_anterior(
            date(2024, 8, 1),
            "Preenchimento",
            "1000",
            "400",
            date(2026, 10, 15),
            date(2024, 8, 1),
            paciente,
        )
        self.assertEqual(nome, "Preenchimento")
        self.assertEqual(valor, Decimal("1000.00"))
        self.assertEqual(pago, Decimal("400.00"))
        self.assertEqual(data_pago, date(2024, 8, 1))
        self.assertEqual(vencimento, date(2026, 10, 25))

    def test_diferenca_semanal_vence_em_sete_dias(self):
        paciente = Patient(prazo_pagamento_modo="SEMANAL")
        _nome, _valor, _pago, _data_pago, vencimento = validar_lancamento_anterior(
            date(2024, 8, 1),
            "Preenchimento",
            "1000",
            "400",
            date(2026, 10, 15),
            date(2024, 8, 1),
            paciente,
        )
        self.assertEqual(vencimento, date(2026, 10, 22))

    def test_diferenca_sem_prazo_recusa(self):
        with self.assertRaises(ValueError):
            validar_lancamento_anterior(
                date(2024, 8, 1), "Botox", "200", "50", date(2026, 10, 15), date(2024, 8, 1), Patient(),
            )

    def test_valor_pago_sem_data_recusa(self):
        paciente = Patient(prazo_pagamento_modo="DIA_FIXO", prazo_pagamento_dia_mes=10)
        with self.assertRaises(ValueError):
            validar_lancamento_anterior(
                date(2024, 8, 1), "Botox", "200", "50", date(2026, 10, 15), None, paciente,
            )

    def test_quitado_nao_tem_vencimento(self):
        _nome, _valor, _pago, data_pago, vencimento = validar_lancamento_anterior(
            date(2024, 8, 1), "Botox", "200", "200", date(2026, 10, 15), date(2024, 8, 2), Patient(),
        )
        self.assertEqual(data_pago, date(2024, 8, 2))
        self.assertIsNone(vencimento)
