"""Valores de proposta e contrato na tela de assinatura, sem gravar documento."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from django.test import SimpleTestCase

from crm_vendas.assinatura_publica_helpers import (
    calcular_valor_por_recorrencia,
    ip_cliente_assinatura,
    montar_json_documento_assinatura,
)


def _item(quantidade, preco, recorrencia):
    return SimpleNamespace(
        quantidade=quantidade,
        preco_unitario=preco,
        produto_servico=SimpleNamespace(recorrencia=recorrencia),
    )


class ValorRecorrenciaTests(SimpleTestCase):
    def test_soma_so_os_itens_da_recorrencia_pedida(self):
        oportunidade = MagicMock()
        oportunidade.itens.select_related.return_value.all.return_value = [
            _item(2, 10, "mensal"),
            _item(1, 50, "unico"),
        ]
        self.assertEqual(calcular_valor_por_recorrencia(oportunidade, "mensal"), 20.0)
        self.assertEqual(calcular_valor_por_recorrencia(oportunidade, "unico"), 50.0)
        self.assertEqual(calcular_valor_por_recorrencia(None, "mensal"), 0)

    def test_falha_ao_ler_itens_vira_zero(self):
        oportunidade = MagicMock()
        oportunidade.itens.select_related.side_effect = RuntimeError("schema")
        self.assertEqual(calcular_valor_por_recorrencia(oportunidade, "mensal"), 0)


class DocumentoAssinaturaTests(SimpleTestCase):
    def test_contrato_com_desconto_percentual_e_aviso_de_link_anterior(self):
        assinatura = MagicMock()
        assinatura.proposta = None
        assinatura.nome_assinante = "Ana"
        assinatura.tipo = "cliente"
        assinatura.get_tipo_display.return_value = "Cliente"

        documento = MagicMock()
        documento.titulo = "Contrato #2"
        documento.valor_total = "1000.00"
        documento.desconto_valor = 10
        documento.desconto_tipo = "percentual"
        documento.valor_com_desconto = "900.00"
        documento.oportunidade.itens.select_related.return_value.all.return_value = []
        documento.oportunidade.lead = SimpleNamespace(nome="Ana", email="a@b.com", empresa="Felix")
        documento.oportunidade.vendedor = SimpleNamespace(email="v@v.com")

        data = montar_json_documento_assinatura(
            assinatura,
            documento,
            meta={"link_anterior": True, "aviso": "Este link substitui o anterior."},
        )
        self.assertEqual(data["tipo_documento"], "contrato")
        self.assertTrue(data["tem_desconto"])
        self.assertEqual(data["desconto_display"], "10%")
        self.assertEqual(data["valor_com_desconto"], "900.00")
        self.assertTrue(data["link_anterior"])
        self.assertIn("substitui", data["aviso"])

    def test_desconto_em_reais_nao_ganha_porcentagem(self):
        assinatura = MagicMock()
        assinatura.proposta = MagicMock()
        assinatura.nome_assinante = "Ana"
        assinatura.tipo = "vendedor"
        assinatura.get_tipo_display.return_value = "Vendedor"
        documento = assinatura.proposta
        documento.titulo = "Proposta"
        documento.valor_total = "200.00"
        documento.desconto_valor = 25
        documento.desconto_tipo = "valor"
        documento.valor_com_desconto = None
        documento.oportunidade = None

        data = montar_json_documento_assinatura(assinatura, documento)
        self.assertEqual(data["tipo_documento"], "proposta")
        self.assertEqual(data["desconto_display"], "25")
        self.assertEqual(data["valor_com_desconto"], "200.00")
        self.assertEqual(data["lead_nome"], "")


class IpAssinaturaTests(SimpleTestCase):
    def test_primeiro_endereco_do_proxy(self):
        request = MagicMock()
        request.META = {"HTTP_X_FORWARDED_FOR": "203.0.113.8, 10.0.0.1", "REMOTE_ADDR": "127.0.0.1"}
        self.assertEqual(ip_cliente_assinatura(request), "203.0.113.8")
        request.META = {"REMOTE_ADDR": "127.0.0.1"}
        self.assertEqual(ip_cliente_assinatura(request), "127.0.0.1")
