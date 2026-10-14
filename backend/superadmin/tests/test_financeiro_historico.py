"""Histórico de pagamentos e notas da loja no financeiro."""
from datetime import date, datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from superadmin.financeiro_views.helpers import _erro_comprovante_pdf, historico_pagamentos_e_notas
from superadmin.financeiro_views.troca_banco import trocar_banco_assinatura
from superadmin.models import FinanceiroLoja, Loja, NFSeEmitida, PagamentoLoja, PlanoAssinatura, TipoLoja


class HistoricoLojaTest(TestCase):
    def setUp(self):
        tipo = TipoLoja.objects.create(nome="Clínica Hist", slug="clinica-hist", codigo="CLIHIST")
        plano = PlanoAssinatura.objects.create(
            nome="Básico Hist", slug="basico-hist", descricao="Básico", preco_mensal="99.90",
        )
        plano.tipos_loja.add(tipo)
        owner = User.objects.create_user("loja-hist", "loja-hist@lwk.test", "senha-teste")
        self.loja = Loja.objects.create(
            nome="Harmonis",
            slug="clinicaharmonis-hist",
            cpf_cnpj="37302743000199",
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
            asaas_payment_id="pay_hist",
            senha_enviada=True,
        )

    def test_mostra_pago_vencido_e_nota(self):
        pago = PagamentoLoja.objects.create(
            loja=self.loja,
            financeiro=self.financeiro,
            valor="99.90",
            referencia_mes=date(2026, 10, 1),
            status="pago",
            asaas_payment_id="pay_out",
            forma_pagamento="BOLETO",
            data_vencimento=date(2026, 10, 10),
            data_pagamento=timezone.make_aware(datetime(2026, 10, 8, 12, 0)),
        )
        PagamentoLoja.objects.create(
            loja=self.loja,
            financeiro=self.financeiro,
            valor="99.90",
            referencia_mes=date(2026, 9, 1),
            status="pendente",
            asaas_payment_id="pay_set",
            forma_pagamento="BOLETO",
            data_vencimento=date(2026, 9, 10),
        )
        NFSeEmitida.objects.create(
            loja=self.loja,
            pagamento=pago,
            numero_nf="61",
            status="emitida",
            valor="99.90",
            pdf_url="https://nf.example/61.pdf",
        )

        itens = historico_pagamentos_e_notas(self.loja)
        por_mes = {item["mes"]: item for item in itens}

        self.assertEqual(por_mes["out/2026"]["situacao_display"], "Pago do mês")
        self.assertEqual(por_mes["out/2026"]["numero_nf"], "61")
        self.assertEqual(por_mes["out/2026"]["pago_em"], "2026-10-08")
        self.assertEqual(por_mes["out/2026"]["provedor_display"], "Asaas")
        self.assertEqual(por_mes["set/2026"]["situacao_display"], "Vencido")
        self.assertEqual(por_mes["set/2026"]["numero_nf"], "")

    def test_historico_mostra_o_banco_que_gerou_o_boleto(self):
        PagamentoLoja.objects.create(
            loja=self.loja,
            financeiro=self.financeiro,
            valor="99.90",
            referencia_mes=date(2026, 8, 1),
            status="pago",
            asaas_payment_id="pay_ago",
            forma_pagamento="BOLETO",
            data_vencimento=date(2026, 8, 10),
            provedor_boleto="cora",
        )
        itens = historico_pagamentos_e_notas(self.loja)
        self.assertEqual(itens[0]["provedor_display"], "Cora")
        self.assertEqual(itens[0]["provedor_boleto"], "cora")

    def test_troca_com_boleto_aberto_vale_no_proximo_mes(self):
        PagamentoLoja.objects.create(
            loja=self.loja,
            financeiro=self.financeiro,
            valor="99.90",
            referencia_mes=date(2026, 11, 1),
            status="pendente",
            asaas_payment_id="pay_nov",
            forma_pagamento="BOLETO",
            data_vencimento=date(2026, 11, 10),
            provedor_boleto="asaas",
        )
        chamadas = []
        resultado = trocar_banco_assinatura(
            self.loja,
            "cora",
            emitir=lambda loja: chamadas.append(loja.pk) or {"success": True},
        )
        self.loja.refresh_from_db()
        self.assertTrue(resultado["success"])
        self.assertFalse(resultado["boleto_emitido"])
        self.assertEqual(chamadas, [])
        self.assertEqual(self.loja.provedor_boleto_preferido, "cora")
        self.assertIn("próximo mês", resultado["message"])
        self.assertIn("Asaas", resultado["message"])
        self.assertEqual(
            PagamentoLoja.objects.get(asaas_payment_id="pay_nov").provedor_boleto,
            "asaas",
        )

    def test_troca_sem_boleto_emite_no_banco_novo(self):
        PagamentoLoja.objects.create(
            loja=self.loja,
            financeiro=self.financeiro,
            valor="99.90",
            referencia_mes=date(2026, 10, 1),
            status="pago",
            asaas_payment_id="pay_pago",
            forma_pagamento="BOLETO",
            data_vencimento=date(2026, 10, 10),
        )
        resultado = trocar_banco_assinatura(
            self.loja,
            "mercadopago",
            emitir=lambda loja: {
                "success": True,
                "message": "Boleto emitido e enviado para a@b.c.",
                "boleto_url": "https://boleto.example/1",
            },
        )
        self.loja.refresh_from_db()
        self.assertTrue(resultado["boleto_emitido"])
        self.assertEqual(self.loja.provedor_boleto_preferido, "mercadopago")
        self.assertIn("emitido", resultado["message"].lower())

    def test_troca_recusa_banco_invalido_e_o_mesmo_banco(self):
        invalido = trocar_banco_assinatura(self.loja, "c6", emitir=lambda loja: {"success": True})
        self.assertFalse(invalido["success"])
        self.loja.refresh_from_db()
        self.assertEqual(self.loja.provedor_boleto_preferido, "asaas")
        igual = trocar_banco_assinatura(self.loja, "asaas", emitir=lambda loja: {"success": True})
        self.assertFalse(igual["success"])

    def test_recusa_comprovante_que_nao_e_pdf(self):
        from io import BytesIO

        arquivo = BytesIO(b"nao e pdf")
        arquivo.name = "comprovante.txt"
        arquivo.size = 10
        self.assertIn("PDF", _erro_comprovante_pdf(arquivo))
        self.assertEqual(_erro_comprovante_pdf(None), "")
