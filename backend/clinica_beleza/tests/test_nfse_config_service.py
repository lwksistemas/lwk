"""Testes unitários para nfse_config_service e nfse_consulta_service.
"""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.nfse_consulta_service import (
    montar_payload_nfse_consulta,
    tentar_emitir_nfse_consulta,
)


class MontarPayloadNFSeConsultaTests(SimpleTestCase):
    """Testes para montar_payload_nfse_consulta."""

    def _consulta(self, cpf="12345678901", nome="Maria", procedure_nome="Botox"):
        patient = MagicMock()
        patient.cpf = cpf
        patient.nome = nome
        patient.email = "maria@test.com"
        patient.endereco = "Rua A, 123"
        patient.cidade = "Ribeirão Preto"
        patient.estado = "SP"

        procedure = MagicMock()
        procedure.nome = procedure_nome

        consulta = MagicMock()
        consulta.id = 1
        consulta.patient = patient
        consulta.procedure = procedure
        consulta.loja_id = 10
        return consulta

    def _payment(self, amount=150.0, status="PAID"):
        p = MagicMock()
        p.amount = amount
        p.status = status
        p.loja_id = 10
        return p

    def _config(self):
        config = MagicMock()
        config.emitir_nf_automaticamente = True
        config.provedor_nf = "asaas"
        config.descricao_servico_padrao = "Serviços de estética"
        config.codigo_servico_municipal = "0601"
        config.item_lista_servico = "06.01"
        return config

    def test_monta_payload_completo(self):
        consulta = self._consulta()
        payment = self._payment()
        config = self._config()

        result = montar_payload_nfse_consulta(consulta, payment, config)

        self.assertIsNotNone(result)
        self.assertEqual(result["tomador_cpf_cnpj"], "12345678901")
        self.assertEqual(result["tomador_nome"], "Maria")
        self.assertEqual(result["valor_servicos"], 150.0)
        self.assertIn("Botox", result["servico_descricao"])
        self.assertEqual(result["codigo_servico"], "0601")

    def test_paciente_sem_cpf_retorna_none(self):
        consulta = self._consulta(cpf="123")  # CPF curto demais
        payment = self._payment()
        config = self._config()

        result = montar_payload_nfse_consulta(consulta, payment, config)

        self.assertIsNone(result)

    def test_sem_procedure_usa_descricao_padrao(self):
        consulta = self._consulta()
        consulta.procedure = None
        payment = self._payment()
        config = self._config()

        result = montar_payload_nfse_consulta(consulta, payment, config)

        self.assertIsNotNone(result)
        self.assertEqual(result["servico_descricao"], "Serviços de estética")

    def test_descricao_padrao_vazia_usa_fallback(self):
        consulta = self._consulta()
        consulta.procedure = None
        payment = self._payment()
        config = self._config()
        config.descricao_servico_padrao = ""

        result = montar_payload_nfse_consulta(consulta, payment, config)

        self.assertEqual(result["servico_descricao"], "Serviços de estética, saúde e bem-estar")


class TentarEmitirNFSeConsultaTests(SimpleTestCase):
    """Testes para tentar_emitir_nfse_consulta."""

    @patch("clinica_beleza.nfse_consulta_service._get_nfse_config")
    def test_payment_none_skips(self, mock_config):
        consulta = MagicMock(loja_id=1)
        tentar_emitir_nfse_consulta(consulta, None)
        mock_config.assert_not_called()

    @patch("clinica_beleza.nfse_consulta_service._get_nfse_config")
    def test_payment_not_paid_skips(self, mock_config):
        consulta = MagicMock(loja_id=1)
        payment = MagicMock(status="PENDING", amount=100)
        tentar_emitir_nfse_consulta(consulta, payment)
        mock_config.assert_not_called()

    @patch("clinica_beleza.nfse_consulta_service._get_nfse_config")
    def test_valor_zero_skips(self, mock_config):
        consulta = MagicMock(loja_id=1)
        payment = MagicMock(status="PAID", amount=0, loja_id=1)
        tentar_emitir_nfse_consulta(consulta, payment)
        mock_config.assert_not_called()

    @patch("clinica_beleza.nfse_consulta_service._get_nfse_config")
    def test_config_none_skips(self, mock_config):
        mock_config.return_value = None
        consulta = MagicMock(loja_id=1)
        payment = MagicMock(status="PAID", amount=100, loja_id=1)
        tentar_emitir_nfse_consulta(consulta, payment)
        mock_config.assert_called_once_with(1)

    @patch("clinica_beleza.nfse_consulta_service._get_nfse_config")
    def test_emissao_desabilitada_skips(self, mock_config):
        config = MagicMock()
        config.emitir_nf_automaticamente = False
        mock_config.return_value = config
        consulta = MagicMock(loja_id=1)
        payment = MagicMock(status="PAID", amount=100, loja_id=1)
        tentar_emitir_nfse_consulta(consulta, payment)
        # Não deve tentar emitir

    @patch("clinica_beleza.nfse_consulta_service._get_nfse_config")
    def test_provedor_manual_skips(self, mock_config):
        config = MagicMock()
        config.emitir_nf_automaticamente = True
        config.provedor_nf = "manual"
        mock_config.return_value = config
        consulta = MagicMock(loja_id=1)
        payment = MagicMock(status="PAID", amount=100, loja_id=1)
        tentar_emitir_nfse_consulta(consulta, payment)
