"""Property-style tests para helpers puros do relatório de comissões."""
import random
from decimal import Decimal
from unittest import TestCase
from unittest.mock import MagicMock

from clinica_beleza.comissao_relatorio_service import (
    _agrupar_pagamentos_por_agendamento,
    _alocar_valores_pagamento,
    _calcular_comissao_regra,
    _combinar_formas_pagamento,
)


def _comissao(modo: str, valor: str):
    c = MagicMock()
    c.modo = modo
    c.valor = Decimal(valor)
    return c


class ComissaoRelatorioPropertyTest(TestCase):
    def setUp(self):
        self.rng = random.Random(42)

    def test_alocar_valores_preserva_total(self):
        """Property: soma alocada == valor do pagamento (até centavos)."""
        for _ in range(30):
            n = self.rng.randint(1, 4)
            procs = []
            total_proc = Decimal(0)
            for i in range(n):
                v = Decimal(str(round(self.rng.uniform(10, 5000), 2)))
                procs.append({"procedure_id": i + 1, "procedimento_nome": f"P{i}", "valor": v})
                total_proc += v
            valor_consulta = Decimal(str(round(self.rng.uniform(0, 500), 2)))
            total = valor_consulta + total_proc
            vc, vp_map = _alocar_valores_pagamento(total, valor_consulta, procs)
            soma = vc + sum(vp_map.values())
            self.assertEqual(soma, total)

    def test_comissao_percentual_proporcional(self):
        for base in (Decimal(0), Decimal(100), Decimal("237.50")):
            val = _calcular_comissao_regra(_comissao("percentual", "25"), base)
            esperado = (base * Decimal(25) / Decimal(100)).quantize(Decimal("0.01"))
            self.assertEqual(val, esperado)

    def test_combinar_formas_pagamento_unicas(self):
        pagamentos = [
            MagicMock(payment_method="pix"),
            MagicMock(payment_method="cartao"),
            MagicMock(payment_method="pix"),
            MagicMock(payment_method=None),
        ]
        formas = _combinar_formas_pagamento(pagamentos)
        self.assertIn("PIX", formas)
        self.assertIn("Cartão", formas)

    def test_agrupar_pagamentos_por_agendamento(self):
        appt10 = MagicMock(id=10)
        appt20 = MagicMock(id=20)
        p1 = MagicMock(appointment=appt10, amount=Decimal(100))
        p2 = MagicMock(appointment=appt10, amount=Decimal(50))
        p3 = MagicMock(appointment=appt20, amount=Decimal(80))
        grupos = _agrupar_pagamentos_por_agendamento([p1, p2, p3])
        self.assertEqual(len(grupos), 2)
        self.assertEqual(grupos[0]["total_amount"], Decimal(150))
        self.assertEqual(len(grupos[0]["payments"]), 2)
