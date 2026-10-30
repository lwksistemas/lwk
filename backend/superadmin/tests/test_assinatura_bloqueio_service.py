"""Testes do bloqueio por inadimplência de assinatura."""
from datetime import date, timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from superadmin.services.assinatura_bloqueio_service import (
    DAYS_TO_BLOCK,
    DAYS_TO_WARN_BOLETO,
    DAYS_TO_WARN_UI,
    aplicar_bloqueio_inadimplencia_loja,
    check_inadimplencia_block,
    dias_atraso_assinatura,
    loja_deve_estar_bloqueada,
    path_allowed_when_store_blocked,
    situacao_aviso_assinatura,
    situacao_geracao_boleto_assinatura,
)

User = get_user_model()


class TestPathAllowedWhenBlocked(TestCase):
    def test_heartbeat_permitido(self):
        self.assertTrue(path_allowed_when_store_blocked("/api/superadmin/lojas/heartbeat/"))
        self.assertTrue(path_allowed_when_store_blocked("/api/superadmin/lojas/heartbeat"))

    def test_financeiro_permitido(self):
        self.assertTrue(path_allowed_when_store_blocked("/api/superadmin/loja/vendasbeta/financeiro/"))
        self.assertTrue(path_allowed_when_store_blocked("/api/superadmin/loja-financeiro/1/"))
        self.assertTrue(path_allowed_when_store_blocked("/api/superadmin/loja-pagamentos/99/baixar_boleto_pdf/"))

    def test_info_publica_permitido(self):
        self.assertTrue(path_allowed_when_store_blocked("/api/superadmin/lojas/info_publica/"))
        self.assertTrue(path_allowed_when_store_blocked("/api/superadmin/lojas/verificar_senha_provisoria/"))
        self.assertTrue(path_allowed_when_store_blocked("/api/suporte/registrar-erro-frontend/"))

    def test_crm_bloqueado(self):
        self.assertFalse(path_allowed_when_store_blocked("/api/crm-vendas/leads/"))


class TestDiasAtrasoAssinatura(TestCase):
    def test_sem_atraso(self):
        loja = Mock()
        loja.financeiro.data_proxima_cobranca = date.today() + timedelta(days=5)
        with patch("superadmin.models.PagamentoLoja") as mock_pg:
            mock_pg.objects.filter.return_value.order_by.return_value.first.return_value = None
            self.assertEqual(dias_atraso_assinatura(loja), 0)

    def test_atraso_pela_data_proxima_cobranca(self):
        loja = Mock()
        loja.financeiro.data_proxima_cobranca = date.today() - timedelta(days=7)
        with patch("superadmin.models.PagamentoLoja") as mock_pg:
            mock_pg.objects.filter.return_value.order_by.return_value.first.return_value = None
            self.assertEqual(dias_atraso_assinatura(loja), 7)
            self.assertTrue(loja_deve_estar_bloqueada(loja))


class TestSituacaoAvisoAssinatura(TestCase):
    def test_aviso_cinco_dias_antes(self):
        loja = Mock()
        loja.is_blocked = False
        loja.financeiro.data_proxima_cobranca = date.today() + timedelta(days=5)
        with patch(
            "superadmin.services.assinatura_bloqueio_service.dias_atraso_assinatura",
            return_value=0,
        ):
            out = situacao_aviso_assinatura(loja)
        self.assertEqual(out["nivel"], "aviso")
        self.assertEqual(out["dias_restantes"], 5)
        self.assertIn("Faltam 5 dias", out["mensagem"])

    def test_sem_aviso_fora_da_janela(self):
        loja = Mock()
        loja.is_blocked = False
        loja.financeiro.data_proxima_cobranca = date.today() + timedelta(days=DAYS_TO_WARN_UI + 3)
        with patch(
            "superadmin.services.assinatura_bloqueio_service.dias_atraso_assinatura",
            return_value=0,
        ):
            self.assertIsNone(situacao_aviso_assinatura(loja))

    def test_vence_hoje(self):
        loja = Mock()
        loja.is_blocked = False
        loja.financeiro.data_proxima_cobranca = date.today()
        with patch(
            "superadmin.services.assinatura_bloqueio_service.dias_atraso_assinatura",
            return_value=0,
        ):
            out = situacao_aviso_assinatura(loja)
        self.assertEqual(out["nivel"], "urgente")
        self.assertIn("vence hoje", out["mensagem"])


class TestSituacaoGeracaoBoleto(TestCase):
    def test_bloqueia_mais_de_dez_dias_antes(self):
        loja = Mock()
        financeiro = Mock()
        financeiro.data_proxima_cobranca = date.today() + timedelta(days=DAYS_TO_WARN_BOLETO + 5)
        with patch("superadmin.models.PagamentoLoja") as mock_pg:
            mock_pg.objects.filter.return_value.exists.return_value = False
            out = situacao_geracao_boleto_assinatura(loja, financeiro)
        self.assertFalse(out["pode_gerar"])
        self.assertIn("10 dias antes", out["motivo"])

    def test_permite_dentro_da_janela(self):
        loja = Mock()
        financeiro = Mock()
        financeiro.data_proxima_cobranca = date.today() + timedelta(days=5)
        with patch("superadmin.models.PagamentoLoja") as mock_pg:
            mock_pg.objects.filter.return_value.exists.return_value = False
            out = situacao_geracao_boleto_assinatura(loja, financeiro)
        self.assertTrue(out["pode_gerar"])

    def test_bloqueia_com_pagamento_pendente(self):
        loja = Mock()
        financeiro = Mock()
        financeiro.data_proxima_cobranca = date.today() + timedelta(days=2)
        with patch("superadmin.models.PagamentoLoja") as mock_pg:
            mock_pg.objects.filter.return_value.exists.return_value = True
            out = situacao_geracao_boleto_assinatura(loja, financeiro)
        self.assertFalse(out["pode_gerar"])
        self.assertIn("boleto em aberto", out["motivo"])


class TestAplicarBloqueio(TestCase):
    def test_bloqueia_apos_cinco_dias(self):
        loja = Mock()
        loja.id = 1
        loja.slug = "vendasbeta"
        loja.is_blocked = False
        loja.blocked_at = None
        loja.blocked_reason = ""
        loja.days_overdue = 0
        financeiro = Mock()
        financeiro.status_pagamento = "pendente"
        loja.financeiro = financeiro

        with patch(
            "superadmin.services.assinatura_bloqueio_service.dias_atraso_assinatura",
            return_value=DAYS_TO_BLOCK,
        ):
            out = aplicar_bloqueio_inadimplencia_loja(loja, persistir=False)

        self.assertTrue(out["blocked"])
        self.assertTrue(loja.is_blocked)
        self.assertEqual(financeiro.status_pagamento, "suspenso")


class TestCheckInadimplenciaBlock(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = Mock(is_authenticated=True, is_superuser=False, username="owner")

    @patch("core.store_membership.resolve_loja_for_user")
    @patch("core.store_membership.user_belongs_to_store", return_value=True)
    def test_retorna_403_quando_bloqueada(self, _belongs, mock_resolve):
        loja = Mock(slug="vendasbeta", is_blocked=True)
        mock_resolve.return_value = loja
        request = self.factory.get("/api/crm-vendas/leads/")
        request.user = self.user
        request.headers = {"X-Tenant-Slug": "vendasbeta"}

        response = check_inadimplencia_block(request)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 403)

    @patch("core.store_membership.resolve_loja_for_user")
    @patch("core.store_membership.user_belongs_to_store", return_value=True)
    def test_financeiro_liberado(self, _belongs, mock_resolve):
        loja = Mock(slug="vendasbeta", is_blocked=True)
        mock_resolve.return_value = loja
        request = self.factory.get("/api/superadmin/loja/vendasbeta/financeiro/")
        request.user = self.user

        self.assertIsNone(check_inadimplencia_block(request))


class TestDegustacao(TestCase):
    def _loja(self, ate):
        loja = Mock()
        loja.id = 1
        loja.slug = "demo"
        loja.is_blocked = False
        loja.blocked_reason = ""
        financeiro = Mock()
        financeiro.status_pagamento = "degustacao"
        financeiro.degustacao_ate = ate
        financeiro.degustacao_avisada = False
        loja.financeiro = financeiro
        return loja, financeiro

    def test_aberta_nao_bloqueia_nem_muda_status(self):
        loja, financeiro = self._loja(date.today() + timedelta(days=10))
        out = aplicar_bloqueio_inadimplencia_loja(loja, persistir=False)
        self.assertFalse(out["blocked"])
        self.assertEqual(financeiro.status_pagamento, "degustacao")
        self.assertFalse(loja.is_blocked)

    def test_encerrada_bloqueia_sem_virar_cobranca(self):
        loja, financeiro = self._loja(date.today() - timedelta(days=1))
        out = aplicar_bloqueio_inadimplencia_loja(loja, persistir=False)
        self.assertTrue(loja.is_blocked)
        self.assertEqual(loja.blocked_reason, "Demonstração encerrada")
        self.assertEqual(financeiro.status_pagamento, "degustacao")
        self.assertEqual(out["reason"], "degustacao_encerrada")

    def test_nao_gera_boleto_enquanto_aberta(self):
        loja, financeiro = self._loja(date.today() + timedelta(days=3))
        out = situacao_geracao_boleto_assinatura(loja, financeiro)
        self.assertFalse(out["pode_gerar"])

    def test_pagar_antes_do_fim_nao_cria_boleto(self):
        from superadmin.degustacao_service import aceitar_boleto_degustacao

        loja, financeiro = self._loja(date.today() + timedelta(days=2))
        with patch("superadmin.cobranca_service.CobrancaService") as cobranca:
            out = aceitar_boleto_degustacao(loja, financeiro)
        self.assertFalse(out["success"])
        cobranca.assert_not_called()

    def test_pagar_depois_do_fim_cria_boleto(self):
        from superadmin.degustacao_service import aceitar_boleto_degustacao

        loja, financeiro = self._loja(date.today() - timedelta(days=1))
        financeiro.boleto_url = "https://boleto.exemplo"
        with (
            patch("superadmin.cobranca_service.CobrancaService") as cobranca,
            patch("superadmin.cobranca_service.cobranca_ja_registrada", return_value=False),
            patch("superadmin.serializers.loja._enviar_boleto_do_cadastro"),
            patch(
                "superadmin.services.financeiro_service.FinanceiroService.calcular_primeiro_vencimento",
                return_value=date.today(),
            ),
        ):
            cobranca.return_value.criar_cobranca.return_value = {"success": True}
            out = aceitar_boleto_degustacao(loja, financeiro)
        self.assertTrue(out["success"])
        cobranca.return_value.criar_cobranca.assert_called_once()
        self.assertEqual(financeiro.status_pagamento, "pendente")


class TestDegustacaoLojaExistente(TestCase):
    def test_sem_boleto_comeca_agora(self):
        from superadmin.degustacao_service import definir_degustacao_loja_existente

        loja = Mock(is_blocked=False, blocked_reason="", slug="demo")
        financeiro = Mock(
            status_pagamento="ativo",
            senha_enviada=True,
            boleto_url="",
            asaas_payment_id="",
            mercadopago_payment_id="",
            cora_invoice_id="",
            degustacao_ate=None,
        )
        with (
            patch("superadmin.financeiro_views.troca_banco.boleto_em_aberto", return_value=None),
            patch("superadmin.degustacao_service.iniciar_contagem_degustacao") as iniciar,
        ):
            out = definir_degustacao_loja_existente(loja, financeiro, 15)
        iniciar.assert_called_once_with(loja, financeiro, 15)
        self.assertTrue(out["success"])
        self.assertFalse(out["aguardando_pagamento"])

    def test_com_boleto_espera_o_pagamento(self):
        from superadmin.degustacao_service import definir_degustacao_loja_existente

        loja = Mock(is_blocked=False, blocked_reason="", slug="demo")
        financeiro = Mock(status_pagamento="pendente", degustacao_ate=None)
        with patch("superadmin.financeiro_views.troca_banco.boleto_em_aberto", return_value=Mock()):
            out = definir_degustacao_loja_existente(loja, financeiro, 30)
        self.assertTrue(out["aguardando_pagamento"])
        self.assertEqual(financeiro.degustacao_dias_apos_pagamento, 30)
        financeiro.save.assert_called_once()

    def test_pagamento_confirmado_inicia_a_contagem(self):
        from superadmin.signals.financeiro import on_payment_confirmed

        financeiro = Mock(status_pagamento="ativo", degustacao_dias_apos_pagamento=15, senha_enviada=True)
        financeiro.loja.slug = "demo"
        with patch("superadmin.degustacao_service.iniciar_contagem_degustacao") as iniciar:
            on_payment_confirmed(sender=None, instance=financeiro, created=False)
        iniciar.assert_called_once_with(financeiro.loja, financeiro, 15)


