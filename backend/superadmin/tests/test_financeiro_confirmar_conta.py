"""PIX ou transferência na conta da empresa dá baixa no boleto Asaas."""
from datetime import date
from io import BytesIO
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase

from superadmin.models import FinanceiroLoja, Loja, PagamentoLoja, PlanoAssinatura, TipoLoja
from superadmin.sync_service.asaas import AsaasSyncService

E2E = "E12345678202610191200ABCDEFGHIJK"


def pdf_comprovante(linhas: list[str]) -> BytesIO:
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    pagina = canvas.Canvas(buffer)
    altura = 800
    for linha in linhas:
        pagina.drawString(40, altura, linha)
        altura -= 18
    pagina.save()
    arquivo = BytesIO(buffer.getvalue())
    arquivo.name = "comprovante.pdf"
    return arquivo


def comprovante_harmonis() -> BytesIO:
    return pdf_comprovante([
        "Pagador HARMONIS CLINICA",
        "CNPJ 37.302.743/0001-99",
        "Valor R$ 99,90",
        f"ID {E2E}",
    ])


class ConfirmarPagamentoContaTest(TestCase):
    def setUp(self):
        tipo = TipoLoja.objects.create(nome="Clínica Beleza Pix", slug="clinica-beleza-pix", codigo="CLIBELPIX")
        plano = PlanoAssinatura.objects.create(
            nome="Básico Pix", slug="basico-pix", descricao="Básico", preco_mensal="99.90",
        )
        plano.tipos_loja.add(tipo)
        owner = User.objects.create_user("loja-pix", "loja-pix@lwk.test", "senha-teste")
        self.loja = Loja.objects.create(
            nome="Harmonis",
            slug="clinicaharmonis-pix",
            cpf_cnpj="37302743000199",
            tipo_loja=tipo,
            plano=plano,
            owner=owner,
            provedor_boleto_preferido="asaas",
        )
        self.financeiro = FinanceiroLoja.objects.create(
            loja=self.loja,
            data_proxima_cobranca=date(2026, 11, 17),
            valor_mensalidade="99.90",
            dia_vencimento=17,
            asaas_payment_id="pay_ja_usado",
            senha_enviada=True,
            status_pagamento="pendente",
        )
        self.pagamento = PagamentoLoja.objects.create(
            loja=self.loja,
            financeiro=self.financeiro,
            valor="99.90",
            referencia_mes=date(2026, 11, 1),
            status="pendente",
            asaas_payment_id="pay_aberto",
            forma_pagamento="BOLETO",
            data_vencimento=date(2026, 11, 17),
        )

    @patch("core.media_storage.media_upload", return_value="https://media.example/comprovante.pdf")
    @patch("superadmin.sync_service.asaas.AsaasSyncService._enviar_email_confirmacao_pagamento")
    @patch("superadmin.sync_service.asaas.tentar_emitir_nfse_assinatura")
    @patch("asaas_integration.client.AsaasClient.listar_transacoes_pix")
    @patch("asaas_integration.client.AsaasClient.receive_payment_in_cash")
    @patch("asaas_integration.client.AsaasClient.get_payment")
    @patch("asaas_integration.models.AsaasConfig.effective_sandbox", return_value=False)
    @patch("asaas_integration.models.AsaasConfig.resolve_api_key", return_value="$aact_prod_teste")
    def test_pix_da_baixa_e_atualiza_assinatura(self, _key, _sandbox, get_payment, receive, pix, _nfse, _email, _upload):
        get_payment.return_value = {"id": "pay_aberto", "status": "PENDING", "value": 99.9, "dueDate": "2026-11-17"}
        receive.return_value = {"id": "pay_aberto", "status": "RECEIVED_IN_CASH", "value": 99.9}
        pix.return_value = {"data": [{
            "id": "pix_1",
            "endToEndIdentifier": E2E,
            "value": 99.9,
            "status": "DONE",
            "type": "CREDIT",
            "externalAccount": {"name": "HARMONIS CLINICA", "cpfCnpj": "37302743000199"},
        }]}

        resultado = AsaasSyncService().confirmar_recebimento_conta_empresa(
            self.loja, "pix", comprovante=comprovante_harmonis(),
        )

        self.assertTrue(resultado["success"], resultado)
        receive.assert_called_once()
        self.pagamento.refresh_from_db()
        self.financeiro.refresh_from_db()
        self.assertEqual(self.pagamento.status, "pago")
        self.assertEqual(self.pagamento.forma_pagamento, "pix")
        self.assertIn("credito:pix_1", self.pagamento.observacoes)
        self.assertEqual(self.financeiro.status_pagamento, "ativo")
        self.assertGreater(self.financeiro.data_proxima_cobranca, date(2026, 11, 17))

    @patch("asaas_integration.client.AsaasClient.receive_payment_in_cash")
    @patch("asaas_integration.models.AsaasConfig.resolve_api_key", return_value="$aact_prod_teste")
    def test_comprovante_de_outro_cnpj_nao_baixa(self, _key, receive):
        arquivo = pdf_comprovante([
            "Pagador OUTRA EMPRESA",
            "CNPJ 11.222.333/0001-81",
            "Valor R$ 99,90",
            f"ID {E2E}",
        ])

        resultado = AsaasSyncService().confirmar_recebimento_conta_empresa(self.loja, "pix", comprovante=arquivo)

        self.assertFalse(resultado["success"])
        self.assertIn("CPF ou CNPJ", resultado["error"])
        receive.assert_not_called()

    @patch("asaas_integration.client.AsaasClient.receive_payment_in_cash")
    @patch("asaas_integration.models.AsaasConfig.resolve_api_key", return_value="$aact_prod_teste")
    def test_sem_boleto_aberto_nao_chama_asaas(self, _key, receive):
        self.pagamento.status = "pago"
        self.pagamento.save(update_fields=["status"])
        PagamentoLoja.objects.create(
            loja=self.loja,
            financeiro=self.financeiro,
            valor="99.90",
            referencia_mes=date(2026, 10, 1),
            status="pago",
            asaas_payment_id="pay_ja_usado",
            forma_pagamento="BOLETO",
            data_vencimento=date(2026, 10, 17),
        )

        resultado = AsaasSyncService().confirmar_recebimento_conta_empresa(self.loja, "transferencia")

        self.assertFalse(resultado["success"])
        receive.assert_not_called()

    @patch("core.media_storage.media_upload", return_value="https://media.example/comprovante.pdf")
    @patch("superadmin.sync_service.asaas.AsaasSyncService._enviar_email_confirmacao_pagamento")
    @patch("superadmin.sync_service.asaas.tentar_emitir_nfse_assinatura")
    @patch("asaas_integration.client.AsaasClient.listar_transacoes_pix")
    @patch("asaas_integration.client.AsaasClient.receive_payment_in_cash")
    @patch("asaas_integration.client.AsaasClient.get_payment")
    @patch("asaas_integration.models.AsaasConfig.effective_sandbox", return_value=False)
    @patch("asaas_integration.models.AsaasConfig.resolve_api_key", return_value="$aact_prod_teste")
    def test_pix_grava_comprovante_pdf(self, _key, _sandbox, get_payment, receive, pix, _nfse, _email, upload):
        get_payment.return_value = {"id": "pay_aberto", "status": "PENDING", "value": 99.9, "dueDate": "2026-11-17"}
        receive.return_value = {"id": "pay_aberto", "status": "RECEIVED_IN_CASH", "value": 99.9}
        pix.return_value = {"data": [{
            "id": "pix_1",
            "endToEndIdentifier": E2E,
            "value": 99.9,
            "status": "DONE",
            "type": "CREDIT",
            "externalAccount": {"name": "HARMONIS CLINICA", "cpfCnpj": "37302743000199"},
        }]}
        arquivo = comprovante_harmonis()

        resultado = AsaasSyncService().confirmar_recebimento_conta_empresa(self.loja, "pix", comprovante=arquivo)

        self.assertTrue(resultado["success"], resultado)
        self.assertIn("Comprovante anexado", resultado["message"])
        upload.assert_called_once()
        self.pagamento.refresh_from_db()
        self.assertEqual(self.pagamento.comprovante, "https://media.example/comprovante.pdf")

    @patch("core.media_storage.media_upload", return_value="https://media.example/comprovante.pdf")
    @patch("superadmin.cora_service.cliente_da_config")
    @patch(
        "superadmin.cora_service.receber_na_conta_empresa",
        return_value={"success": True, "processed": True, "payment_id": "inv_cora"},
    )
    def test_conta_da_empresa_na_cora_nao_usa_asaas(self, receber, cliente_da_config, _upload):
        client = MagicMock()
        client.consultar_extrato.return_value = [{
            "id": "ent_1",
            "type": "CREDIT",
            "amount": 9990,
            "transaction": {
                "id": "trx_1",
                "type": "TRANSFER",
                "description": "Transferencia HARMONIS",
                "counterParty": {"name": "HARMONIS CLINICA", "identity": "37302743000199"},
            },
        }]
        cliente_da_config.return_value = (client, None)
        self.financeiro.provedor_boleto = "cora"
        self.financeiro.cora_invoice_id = "inv_cora"
        self.financeiro.save(update_fields=["provedor_boleto", "cora_invoice_id"])
        self.pagamento.provedor_boleto = "cora"
        self.pagamento.cora_invoice_id = "inv_cora"
        self.pagamento.asaas_payment_id = ""
        self.pagamento.save(update_fields=["provedor_boleto", "cora_invoice_id", "asaas_payment_id"])

        resultado = AsaasSyncService().confirmar_recebimento_conta_empresa(
            self.loja, "transferencia", comprovante=comprovante_harmonis(),
        )

        self.assertTrue(resultado["success"], resultado)
        self.assertIn("Cora", resultado["message"])
        receber.assert_called_once_with("inv_cora", "transferencia")
        self.pagamento.refresh_from_db()
        self.assertIn("credito:ent_1", self.pagamento.observacoes)
