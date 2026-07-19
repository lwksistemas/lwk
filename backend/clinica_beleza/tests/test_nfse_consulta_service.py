"""Testes do serviço NFS-e ao finalizar consulta."""

from decimal import Decimal
from unittest import TestCase
from unittest.mock import MagicMock, patch

from clinica_beleza.nfse_consulta_service import (
    emitir_nfse_consulta_manual,
    montar_payload_nfse_consulta,
    tentar_emitir_nfse_consulta,
)


class NFSeConsultaServiceTest(TestCase):
    def _consulta(self, **kwargs):
        patient = MagicMock()
        patient.nome = kwargs.get("nome", "Maria Silva")
        patient.cpf = kwargs.get("cpf", "12345678901")
        patient.email = kwargs.get("email", "maria@test.com")
        patient.endereco = kwargs.get("endereco", "Rua A, 10")
        patient.cidade = kwargs.get("cidade", "São Paulo")
        patient.estado = kwargs.get("estado", "SP")

        procedure = MagicMock()
        procedure.nome = kwargs.get("proc_nome", "Limpeza de pele")

        consulta = MagicMock()
        consulta.id = 1
        consulta.loja_id = 10
        consulta.patient = patient
        consulta.procedure = procedure if kwargs.get("com_procedure", True) else None
        return consulta

    def _payment(self, **kwargs):
        payment = MagicMock()
        payment.status = kwargs.get("status", "PAID")
        payment.amount = Decimal(str(kwargs.get("amount", "150.00")))
        payment.loja_id = 10
        return payment

    def _config(self, **kwargs):
        config = MagicMock()
        config.emitir_nf_automaticamente = kwargs.get("auto", True)
        config.provedor_nf = kwargs.get("provedor", "issnet")
        config.descricao_servico_padrao = "Serviços estéticos"
        config.codigo_servico_municipal = "0601"
        config.item_lista_servico = "06.01"
        return config

    def test_montar_payload_com_procedimento(self):
        payload = montar_payload_nfse_consulta(
            self._consulta(),
            self._payment(),
            self._config(),
        )
        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload["tomador_cpf_cnpj"], "12345678901")
        self.assertIn("Limpeza de pele", payload["servico_descricao"])
        self.assertEqual(payload["valor_servicos"], Decimal("150.00"))

    def test_montar_payload_sem_cpf_retorna_none(self):
        payload = montar_payload_nfse_consulta(
            self._consulta(cpf=""),
            self._payment(),
            self._config(),
        )
        self.assertIsNone(payload)

    @patch("nfse_integration.loja_nfse_api.processar_emissao_nfse_loja")
    @patch("clinica_beleza.nfse_consulta_service._get_nfse_config")
    @patch("superadmin.models.Loja")
    def test_emite_quando_pago_e_config_ativa(self, mock_loja, mock_get_config, mock_processar):
        mock_get_config.return_value = self._config()
        mock_loja.objects.using.return_value.filter.return_value.first.return_value = MagicMock(id=10)
        mock_processar.return_value = ({"success": True, "message": "ok"}, 201)

        tentar_emitir_nfse_consulta(self._consulta(), self._payment())

        mock_processar.assert_called_once()

    @patch("nfse_integration.loja_nfse_api.processar_emissao_nfse_loja")
    @patch("clinica_beleza.nfse_consulta_service._get_nfse_config")
    @patch("superadmin.models.Loja")
    def test_enfileira_quando_fila_ativa(self, mock_loja, mock_get_config, mock_processar):
        loja = MagicMock(id=10)
        mock_get_config.return_value = self._config()
        mock_loja.objects.using.return_value.filter.return_value.first.return_value = loja
        mock_processar.return_value = (
            {"success": True, "queued": True, "message": "enfileirada"},
            202,
        )

        tentar_emitir_nfse_consulta(self._consulta(), self._payment())

        mock_processar.assert_called_once()
        self.assertEqual(mock_processar.call_args[0][1], 10)

    @patch("nfse_integration.loja_nfse_api.processar_emissao_nfse_loja")
    @patch("clinica_beleza.nfse_consulta_service._get_nfse_config")
    def test_nao_emite_se_provedor_desabilitado(self, mock_get_config, mock_processar):
        mock_get_config.return_value = self._config(provedor="desabilitado")

        tentar_emitir_nfse_consulta(self._consulta(), self._payment())

        mock_processar.assert_not_called()

    @patch("nfse_integration.loja_nfse_api.processar_emissao_nfse_loja")
    @patch("clinica_beleza.nfse_consulta_service._get_nfse_config")
    @patch("superadmin.models.Loja")
    def test_manual_emite_mesmo_com_auto_desligada(self, mock_loja, mock_get_config, mock_processar):
        mock_get_config.return_value = self._config(auto=False)
        mock_loja.objects.using.return_value.filter.return_value.first.return_value = MagicMock(id=10)
        mock_processar.return_value = ({"success": True, "message": "ok"}, 201)

        result = emitir_nfse_consulta_manual(self._consulta(), self._payment())

        self.assertTrue(result["success"])
        mock_processar.assert_called_once()

    @patch("clinica_beleza.consulta_service._garantir_valor_consulta_consulta")
    @patch("clinica_beleza.consulta_service._valor_pagamento_padrao", return_value=Decimal(100))
    @patch("clinica_beleza.nfse_consulta_service.tentar_emitir_nfse_consulta")
    @patch("clinica_beleza.consulta_service.calcular_comissao_payment_atendimento", return_value=(None, None))
    @patch("clinica_beleza.consulta_service.Payment")
    def test_finalizar_chama_nfse_quando_pago(self, mock_payment_cls, _comissao, mock_nfse, _valor, _garantir):
        from clinica_beleza.consulta_service import _ensure_payment_for_appointment

        appointment = MagicMock()
        appointment.loja_id = 10
        consulta = MagicMock()
        consulta.loja_id = 10

        mock_payment_cls.objects.filter.return_value.first.return_value = None
        mock_payment_cls.objects.create.return_value = MagicMock(status="PAID", amount=Decimal(100))

        _ensure_payment_for_appointment(
            appointment, consulta, payment_method="PIX", mark_as_paid=True, amount=100,
        )

        mock_nfse.assert_called_once()
