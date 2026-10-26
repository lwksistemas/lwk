"""Smoke dos helpers de assinatura pública."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from django.test import SimpleTestCase

from crm_vendas.assinatura_publica_helpers import (
    decodificar_payload_token_assinatura,
    json_erro_assinatura_publica,
    montar_json_documento_assinatura,
    status_http_erro_tenant,
)


class DecodificarTokenAssinaturaSmokeTest(SimpleTestCase):
    def test_token_malformado_retorna_erro(self):
        payload, err = decodificar_payload_token_assinatura("nao-e-um-token-valido")
        self.assertIsNone(payload)
        self.assertIsNotNone(err)

    def test_json_erro_inclui_mensagem(self):
        resp = json_erro_assinatura_publica("Link inválido", error_code="invalido")
        self.assertEqual(resp.status_code, 400)
        import json

        body = json.loads(resp.content)
        self.assertEqual(body["error"], "Link inválido")
        self.assertEqual(body["error_code"], "invalido")


class MontarJsonDocumentoAssinaturaSmokeTest(SimpleTestCase):
    def test_monta_payload_proposta_basico(self):
        assinatura = MagicMock()
        assinatura.proposta = MagicMock()
        assinatura.contrato = None
        assinatura.nome_assinante = "Cliente Teste"
        assinatura.tipo = "cliente"
        assinatura.get_tipo_display.return_value = "Cliente"

        documento = assinatura.proposta
        documento.titulo = "Proposta #1"
        documento.valor_total = "1000.00"
        documento.desconto_valor = 0
        documento.desconto_tipo = "percentual"
        documento.valor_com_desconto = None
        documento.oportunidade = MagicMock()
        documento.oportunidade.lead = MagicMock(nome="Lead", email="a@b.com", empresa="")
        documento.oportunidade.vendedor = MagicMock(email="v@v.com", nome="Luiz Henrique Felix")
        documento.oportunidade.itens.select_related.return_value.all.return_value = []

        data = montar_json_documento_assinatura(assinatura, documento)
        self.assertEqual(data["tipo_documento"], "proposta")
        self.assertEqual(data["titulo"], "Proposta #1")
        self.assertEqual(data["lead_nome"], "Lead")
        self.assertEqual(data["vendedor_nome"], "Luiz Henrique Felix")
        self.assertEqual(data["vendedor_email"], "v@v.com")


class Relacao(list):
    def filter(self, **kwargs):
        return self

    def order_by(self, *args):
        return self


class ConfirmacaoDuasPartesTest(SimpleTestCase):
    def test_mostra_vendedor_cliente_e_libera_o_pdf(self):
        from datetime import datetime

        from django.utils import timezone

        from crm_vendas.assinatura_publica_helpers import confirmacao_crm_ja_assinado

        quando_vendedor = timezone.make_aware(datetime(2026, 10, 23, 7, 20))
        quando_cliente = timezone.make_aware(datetime(2026, 10, 23, 7, 27))
        vendedor = SimpleNamespace(
            tipo="vendedor",
            assinado=True,
            nome_assinante="LUIZ HENRIQUE FELIX",
            assinado_em=quando_vendedor,
        )
        cliente = SimpleNamespace(
            tipo="cliente",
            assinado=True,
            nome_assinante="SAMUEL MARQUES BORGES",
            assinado_em=quando_cliente,
        )
        documento = SimpleNamespace(
            loja_id=None,
            oportunidade=SimpleNamespace(empresa_prestadora=SimpleNamespace(logo="", nome="ULTRASIS")),
            assinaturas=Relacao([vendedor, cliente]),
        )
        assinatura = SimpleNamespace(
            proposta_id=307,
            proposta=documento,
            contrato_id=None,
            contrato=None,
            tipo="cliente",
            assinado=True,
            nome_assinante="SAMUEL MARQUES BORGES",
            assinado_em=quando_cliente,
        )
        dados = confirmacao_crm_ja_assinado(assinatura)
        self.assertTrue(dados["assinado_pelas_duas_partes"])
        self.assertTrue(dados["pode_baixar_pdf"])
        self.assertIn("pelas duas partes", dados["mensagem"])
        self.assertEqual(
            [(parte["papel"], parte["nome"], parte["hora"]) for parte in dados["assinaturas"]],
            [("Vendedor", "LUIZ HENRIQUE FELIX", "07:20"), ("Cliente", "SAMUEL MARQUES BORGES", "07:27")],
        )
        self.assertEqual(dados["nome_prestadora"], "ULTRASIS")

    def test_so_uma_parte_mantem_a_mensagem_de_quem_assinou(self):
        from datetime import datetime

        from django.utils import timezone

        from crm_vendas.assinatura_publica_helpers import (
            confirmacao_crm_ja_assinado,
            resposta_pdf_assinado_pelas_duas_partes,
        )

        quando = timezone.make_aware(datetime(2026, 10, 23, 7, 27))
        cliente = SimpleNamespace(
            tipo="cliente",
            assinado=True,
            nome_assinante="SAMUEL MARQUES BORGES",
            assinado_em=quando,
        )
        documento = SimpleNamespace(loja_id=None, oportunidade=None, assinaturas=Relacao([cliente]))
        assinatura = SimpleNamespace(
            proposta_id=1,
            proposta=documento,
            contrato_id=None,
            contrato=None,
            tipo="cliente",
            assinado=True,
            nome_assinante="SAMUEL MARQUES BORGES",
            assinado_em=quando,
        )
        dados = confirmacao_crm_ja_assinado(assinatura)
        self.assertNotIn("assinado_pelas_duas_partes", dados)
        self.assertIn("SAMUEL MARQUES BORGES", dados["mensagem"])
        self.assertIn("23/10/2026 às 07:27", dados["mensagem"])
        self.assertIsNone(resposta_pdf_assinado_pelas_duas_partes(assinatura))


class StatusHttpErroTenantSmokeTest(SimpleTestCase):
    def test_indisponivel_retorna_503(self):
        self.assertEqual(status_http_erro_tenant("Serviço indisponível"), 503)

    def test_outro_erro_retorna_400(self):
        self.assertEqual(status_http_erro_tenant("Loja inválida"), 400)
