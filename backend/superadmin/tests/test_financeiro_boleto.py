"""Emitir e reenviar boleto da assinatura."""
from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from superadmin.models import FinanceiroLoja, Loja, PagamentoLoja, PlanoAssinatura, TipoLoja
from superadmin.sync_service.asaas import AsaasSyncService


class BoletoAssinaturaTest(TestCase):
    def setUp(self):
        tipo = TipoLoja.objects.create(nome="Clínica Boleto", slug="clinica-boleto", codigo="CLIBOL")
        plano = PlanoAssinatura.objects.create(
            nome="Básico Bol", slug="basico-bol", descricao="Básico", preco_mensal="99.90",
        )
        plano.tipos_loja.add(tipo)
        owner = User.objects.create_user("loja-bol", "loja-bol@lwk.test", "senha-teste")
        self.loja = Loja.objects.create(
            nome="Harmonis",
            slug="clinicaharmonis-bol",
            cpf_cnpj="37302743000188",
            tipo_loja=tipo,
            plano=plano,
            owner=owner,
            provedor_boleto_preferido="asaas",
        )
        self.financeiro = FinanceiroLoja.objects.create(
            loja=self.loja,
            data_proxima_cobranca=date(2026, 12, 1),
            valor_mensalidade="99.90",
            dia_vencimento=1,
            asaas_payment_id="pay_antigo",
            senha_enviada=True,
            boleto_url="https://asaas.example/boleto-antigo",
        )
        self.pagamento = PagamentoLoja.objects.create(
            loja=self.loja,
            financeiro=self.financeiro,
            valor="99.90",
            referencia_mes=date(2026, 12, 1),
            status="pendente",
            asaas_payment_id="pay_aberto",
            forma_pagamento="BOLETO",
            boleto_url="https://asaas.example/boleto-aberto",
            data_vencimento=date(2026, 12, 1),
        )

    @patch("superadmin.boleto_email.baixar_pdf_boleto", return_value=b"%PDF-1.4 boleto")
    @patch("core.email_delivery.send_prepared")
    def test_reenviar_manda_o_boleto_aberto(self, send_prepared, _pdf):
        resultado = AsaasSyncService().reenviar_boleto(self.loja)
        self.assertTrue(resultado["success"], resultado)
        self.assertEqual(resultado["boleto_url"], "https://asaas.example/boleto-aberto")
        send_prepared.assert_called_once()
        mensagem = send_prepared.call_args.args[0]
        self.assertIn("boleto-aberto", mensagem.body)
        self.assertIn("anexo", mensagem.body)
        self.assertEqual(mensagem.to, ["loja-bol@lwk.test"])
        self.assertEqual(mensagem.attachments[0][0], "boleto-lwk.pdf")
        self.assertEqual(mensagem.attachments[0][2], "application/pdf")

    @patch("superadmin.cobranca_service.CobrancaService.criar_cobranca")
    def test_emitir_nao_duplica_boleto_aberto(self, criar):
        resultado = AsaasSyncService().emitir_boleto(self.loja)
        self.assertFalse(resultado["success"])
        criar.assert_not_called()

    @patch("superadmin.sync_service.asaas.AsaasSyncService._enviar_email_boleto", return_value=(True, "loja-bol@lwk.test"))
    @patch("superadmin.cobranca_service.CobrancaService.criar_cobranca")
    def test_emitir_quando_nao_ha_boleto(self, criar, _email):
        self.pagamento.status = "pago"
        self.pagamento.save(update_fields=["status"])
        PagamentoLoja.objects.create(
            loja=self.loja,
            financeiro=self.financeiro,
            valor="99.90",
            referencia_mes=date(2026, 11, 1),
            status="pago",
            asaas_payment_id="pay_antigo",
            forma_pagamento="BOLETO",
            data_vencimento=date(2026, 11, 1),
        )
        criar.return_value = {
            "success": True,
            "boleto_url": "https://asaas.example/boleto-novo",
            "due_date": "2026-12-01",
        }

        resultado = AsaasSyncService().emitir_boleto(self.loja)

        self.assertTrue(resultado["success"], resultado)
        criar.assert_called_once()
        self.assertIn("loja-bol@lwk.test", resultado["message"])
