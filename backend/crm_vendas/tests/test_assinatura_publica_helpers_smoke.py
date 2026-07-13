"""Smoke dos helpers de assinatura pública."""
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
        documento.oportunidade.vendedor = MagicMock(email="v@v.com")
        documento.oportunidade.itens.select_related.return_value.all.return_value = []

        data = montar_json_documento_assinatura(assinatura, documento)
        self.assertEqual(data["tipo_documento"], "proposta")
        self.assertEqual(data["titulo"], "Proposta #1")
        self.assertEqual(data["lead_nome"], "Lead")


class StatusHttpErroTenantSmokeTest(SimpleTestCase):
    def test_indisponivel_retorna_503(self):
        self.assertEqual(status_http_erro_tenant("Serviço indisponível"), 503)

    def test_outro_erro_retorna_400(self):
        self.assertEqual(status_http_erro_tenant("Loja inválida"), 400)
