"""Valor pago pela prestadora e percentual do vendedor."""
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from crm_vendas.comissao_prestadora_service import (
    comissao_do_vendedor,
    mapa_comissao_dos_vendedores,
    parte_comissao_item,
    validar_comissoes_categoria,
    validar_itens_comissao,
)


class ComissaoPrestadoraTest(SimpleTestCase):
    def test_vendedor_recebe_o_percentual_sobre_o_valor_da_prestadora(self):
        self.assertEqual(comissao_do_vendedor(Decimal("375.00"), Decimal("10")), Decimal("37.50"))
        self.assertEqual(comissao_do_vendedor(Decimal("750.00"), 0), Decimal("0.00"))

    def test_servico_em_branco_nao_entra(self):
        itens = validar_itens_comissao([
            {"produto_servico_id": 1, "valor": "375,00"},
            {"produto_servico_id": 2, "valor": ""},
        ])
        self.assertEqual(itens, [{"produto_servico_id": 1, "valor": Decimal("375.00")}])

    def test_valor_negativo_e_recusado(self):
        with self.assertRaises(ValueError):
            validar_itens_comissao([{"produto_servico_id": 1, "valor": "-1"}])

    def test_valor_fixo_da_categoria_e_por_unidade(self):
        parte = parte_comissao_item(
            Decimal("375.00"),
            Decimal("2"),
            {"tipo": "fixo", "valor": Decimal("50.00")},
            Decimal("10"),
        )
        self.assertEqual(parte, Decimal("100.00"))

    def test_porcentagem_da_categoria_incide_sobre_o_valor_da_prestadora(self):
        parte = parte_comissao_item(
            Decimal("375.00"),
            Decimal("1"),
            {"tipo": "percentual", "valor": Decimal("10")},
            Decimal("0"),
        )
        self.assertEqual(parte, Decimal("37.50"))

    def test_categoria_sem_regra_usa_o_percentual_padrao(self):
        parte = parte_comissao_item(Decimal("375.00"), Decimal("1"), None, Decimal("10"))
        self.assertEqual(parte, Decimal("37.50"))

    def test_comissao_de_categoria_em_branco_nao_entra(self):
        itens = validar_comissoes_categoria([
            {"categoria_id": 1, "tipo": "fixo", "valor": "50"},
            {"categoria_id": 2, "tipo": "percentual", "valor": ""},
        ])
        self.assertEqual(itens, [{"categoria_id": 1, "tipo": "fixo", "valor": Decimal("50.00")}])

    def test_relatorio_usa_a_comissao_do_vendedor_pedido(self):
        class Venda:
            def __init__(self, venda_id, vendedor_id):
                self.id = venda_id
                self.vendedor_id = vendedor_id

        felipe = MagicMock()
        felipe.id = 2
        consulta = MagicMock()
        consulta.prefetch_related.return_value = [felipe]
        vendas = [Venda(10, 2), Venda(11, 1)]
        with patch("crm_vendas.models.Vendedor") as modelo, patch(
            "crm_vendas.comissao_prestadora_service.partes_por_oportunidade",
            return_value={10: Decimal("50.00")},
        ) as partes:
            modelo.objects.filter.return_value = consulta
            mapa = mapa_comissao_dos_vendedores(vendas, somente_vendedor_id=2)
        self.assertEqual(mapa, {10: Decimal("50.00")})
        self.assertEqual([venda.id for venda in partes.call_args.args[0]], [10])
