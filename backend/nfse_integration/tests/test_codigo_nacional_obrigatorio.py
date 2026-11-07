"""A loja não emite quando o cTribNac sairia 140101 sem escolha."""
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from nfse_integration.emissao_issnet_nacional_loja import (
    codigo_tributacao_nacional_sefin,
    motivo_codigo_nacional_inventado,
)
from nfse_integration.loja_nfse_api import processar_emissao_nfse_loja
from nfse_integration.service import NFSeService


def _dados():
    return {"servico_descricao": "Consulta", "valor_servicos": "10.00"}


class CodigoNacionalObrigatorioTests(SimpleTestCase):
    def test_vazio_ainda_resolve_140101_e_a_emissao_recusa_antes_do_dps(self):
        config = SimpleNamespace(codigo_servico_municipal="0601")
        self.assertEqual(codigo_tributacao_nacional_sefin(config, "0601"), "140101")
        self.assertIn("14.01", motivo_codigo_nacional_inventado(config, codigo_servico="0601"))

        with (
            patch("nfse_integration.config_loja.config_nfse_da_loja", return_value=config),
            patch("nfse_integration.persistencia_nfse_loja.reservar_emissao_loja") as reservar,
        ):
            body, code = processar_emissao_nfse_loja(SimpleNamespace(id=4), 4, _dados())
        self.assertEqual(code, 400)
        self.assertIn("14.01", body["error"])
        reservar.assert_not_called()

    def test_codigo_nacional_gravado_deixa_reservar(self):
        config = SimpleNamespace(codigo_tributacao_nacional="060201", codigo_servico_municipal="0602")
        self.assertEqual(motivo_codigo_nacional_inventado(config), "")
        reserva = SimpleNamespace(numero_rps=3)
        with (
            patch("nfse_integration.queue_dispatch.should_enqueue_nfse", return_value=True),
            patch("nfse_integration.queue_dispatch.enqueue_emissao_nfse_loja"),
            patch("nfse_integration.config_loja.config_nfse_da_loja", return_value=config),
            patch("nfse_integration.persistencia_nfse_loja.reservar_emissao_loja", return_value=reserva) as reservar,
        ):
            body, code = processar_emissao_nfse_loja(SimpleNamespace(id=4), 4, _dados())
        self.assertEqual(code, 202)
        reservar.assert_called_once()
        self.assertTrue(body["queued"])

    def test_item_da_lista_ou_140101_escolhido_nao_recusa(self):
        por_item = SimpleNamespace(item_lista_servico="06.02", codigo_servico_municipal="0601")
        escolhido = SimpleNamespace(codigo_tributacao_nacional="140101")
        self.assertEqual(motivo_codigo_nacional_inventado(por_item), "")
        self.assertEqual(motivo_codigo_nacional_inventado(escolhido), "")
        self.assertEqual(
            motivo_codigo_nacional_inventado(
                SimpleNamespace(codigo_servico_municipal="0601"),
                codigo_servico="060201",
            ),
            "",
        )

    def test_servico_igual_ao_municipal_continua_inventando(self):
        config = SimpleNamespace(codigo_servico_municipal="1401")
        self.assertIn("14.01", motivo_codigo_nacional_inventado(config, codigo_servico="14.01"))

    def test_servico_nao_reserva_dps_quando_o_codigo_sai_inventado(self):
        service = NFSeService.__new__(NFSeService)
        service.loja = SimpleNamespace(id=4)
        service.config = SimpleNamespace(provedor_nf="nacional", codigo_servico_municipal="0601")
        with (
            patch(
                "nfse_integration.prestador_loja.resolver_prestador_emissao_loja",
                return_value=None,
            ),
            patch("nfse_integration.persistencia_nfse_loja.reservar_emissao_loja") as reservar,
        ):
            resultado = service.emitir_nfse(
                tomador_cpf_cnpj="123",
                tomador_nome="Ana",
                tomador_email="",
                tomador_endereco={},
                servico_descricao="Consulta",
                valor_servicos="10.00",
            )
        self.assertFalse(resultado["success"])
        self.assertIn("14.01", resultado["error"])
        reservar.assert_not_called()
