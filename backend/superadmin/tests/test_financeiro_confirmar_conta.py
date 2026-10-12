"""PIX ou transferência na conta da empresa dá baixa no boleto Asaas."""
from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from superadmin.models import FinanceiroLoja, Loja, PagamentoLoja, PlanoAssinatura, TipoLoja
from superadmin.sync_service.asaas import AsaasSyncService


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

    @patch("superadmin.sync_service.asaas.AsaasSyncService._enviar_email_confirmacao_pagamento")
    @patch("superadmin.sync_service.asaas.tentar_emitir_nfse_assinatura")
    @patch("asaas_integration.client.AsaasClient.receive_payment_in_cash")
    @patch("asaas_integration.client.AsaasClient.get_payment")
    @patch("asaas_integration.models.AsaasConfig.effective_sandbox", return_value=False)
    @patch("asaas_integration.models.AsaasConfig.resolve_api_key", return_value="$aact_prod_teste")
    def test_pix_da_baixa_e_atualiza_assinatura(self, _key, _sandbox, get_payment, receive, _nfse, _email):
        get_payment.return_value = {"id": "pay_aberto", "status": "PENDING", "value": 99.9, "dueDate": "2026-11-17"}
        receive.return_value = {"id": "pay_aberto", "status": "RECEIVED_IN_CASH", "value": 99.9}

        resultado = AsaasSyncService().confirmar_recebimento_conta_empresa(self.loja, "pix")

        self.assertTrue(resultado["success"], resultado)
        receive.assert_called_once()
        self.pagamento.refresh_from_db()
        self.financeiro.refresh_from_db()
        self.assertEqual(self.pagamento.status, "pago")
        self.assertEqual(self.pagamento.forma_pagamento, "pix")
        self.assertEqual(self.financeiro.status_pagamento, "ativo")
        self.assertGreater(self.financeiro.data_proxima_cobranca, date(2026, 11, 17))

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
