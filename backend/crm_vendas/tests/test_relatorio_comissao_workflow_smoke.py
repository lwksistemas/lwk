"""Smoke: workflow de aprovação/assinatura do relatório de comissão."""
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from crm_vendas.relatorio_comissao_workflow import (
    aprovar_relatorio,
    configurar_tenant_relatorio_publico,
    criar_relatorio_comissao,
    extrair_ip_cliente,
    reprovar_relatorio,
    vendedor_assinar_relatorio,
)


def _relatorio_mock(*, status="pendente_aprovacao"):
    ep = MagicMock()
    ep.nome = "Empresa EP"
    ep.email = "ep@example.com"
    ep.cnpj = "12345678000190"

    vendedor = MagicMock()
    vendedor.nome = "Vendedor Um"
    vendedor.email = "vendedor@example.com"

    rel = MagicMock()
    rel.numero = "RC-001"
    rel.loja_id = 4
    rel.status = status
    rel.periodo_descricao = "Junho 2026"
    rel.quantidade_vendas = 2
    rel.valor_total_vendas = Decimal(10000)
    rel.valor_total_comissao = Decimal(1500)
    rel.empresa_prestadora = ep
    rel.vendedor = vendedor
    rel.token_empresa = "tok-emp"
    rel.token_vendedor = "tok-vend"
    rel.pode_aprovar = status == "pendente_aprovacao"
    rel.pode_reprovar = status == "pendente_aprovacao"
    rel.pode_vendedor_assinar = status == "aprovado"
    return rel


class ExtrairIpClienteTest(SimpleTestCase):
    def test_x_forwarded_for(self):
        request = MagicMock()
        request.META = {"HTTP_X_FORWARDED_FOR": "203.0.113.1, 10.0.0.1"}
        self.assertEqual(extrair_ip_cliente(request), "203.0.113.1")

    def test_remote_addr_fallback(self):
        request = MagicMock()
        request.META = {"REMOTE_ADDR": "192.168.1.5"}
        self.assertEqual(extrair_ip_cliente(request), "192.168.1.5")


class AprovarReprovarRelatorioTest(SimpleTestCase):
    @patch("crm_vendas.relatorio_comissao_workflow.enviar_email_vendedor_assinar")
    def test_aprovar_muda_status_e_notifica_vendedor(self, mock_email):
        rel = _relatorio_mock()
        ok, err = aprovar_relatorio(rel, "Maria Aprovadora", "1.2.3.4")
        self.assertTrue(ok)
        self.assertIsNone(err)
        self.assertEqual(rel.status, "aprovado")
        rel.save.assert_called()
        mock_email.assert_called_once_with(rel)

    def test_aprovar_bloqueado_status_errado(self):
        rel = _relatorio_mock(status="aprovado")
        rel.pode_aprovar = False
        ok, err = aprovar_relatorio(rel, "Maria", "1.2.3.4")
        self.assertFalse(ok)
        self.assertIn("status", (err or "").lower())

    def test_reprovar_com_motivo(self):
        rel = _relatorio_mock()
        ok, err = reprovar_relatorio(rel, "Valores divergentes")
        self.assertTrue(ok)
        self.assertEqual(rel.status, "reprovado")
        self.assertEqual(rel.empresa_reprovado_motivo, "Valores divergentes")

    def test_reprovar_bloqueado_status_errado(self):
        rel = _relatorio_mock(status="pago")
        rel.pode_reprovar = False
        ok, err = reprovar_relatorio(rel, "motivo")
        self.assertFalse(ok)


class VendedorAssinarRelatorioTest(SimpleTestCase):
    @patch("crm_vendas.relatorio_comissao_workflow.gerar_boleto_comissao", return_value=(True, None))
    @patch("crm_vendas.relatorio_comissao_workflow.enviar_pdf_assinado")
    def test_assinar_vendedor_gera_boleto(self, _pdf, mock_boleto):
        rel = _relatorio_mock(status="aprovado")
        ok, err = vendedor_assinar_relatorio(rel, "João Vendedor", "5.6.7.8")
        self.assertTrue(ok)
        self.assertEqual(rel.status, "aguardando_pagamento")
        mock_boleto.assert_called_once_with(rel)

    def test_assinar_bloqueado_se_nao_aprovado(self):
        rel = _relatorio_mock(status="pendente_aprovacao")
        rel.pode_vendedor_assinar = False
        ok, err = vendedor_assinar_relatorio(rel, "João", "1.1.1.1")
        self.assertFalse(ok)


@patch("tenants.middleware.set_current_tenant_db")
@patch("tenants.middleware.set_current_loja_id")
@patch("core.db_config.ensure_loja_database_config", return_value=True)
@patch("superadmin.models.Loja")
class ConfigurarTenantRelatorioPublicoTest(SimpleTestCase):
    def test_loja_nao_encontrada(self, mock_loja_cls, *_mocks):
        from django.test import override_settings

        with override_settings(DATABASES={"default": {}, "loja_x": {}}):
            mock_loja_cls.objects.using.return_value.filter.return_value.first.return_value = None
            loja, err = configurar_tenant_relatorio_publico(99)
        self.assertIsNone(loja)
        self.assertIn("inválido", (err or "").lower())

    def test_configura_tenant_com_sucesso(self, mock_loja_cls, _ensure, _set_loja, _set_db):
        from django.test import override_settings

        loja = MagicMock()
        loja.slug = "felix"
        loja.database_name = "loja_x"
        mock_loja_cls.objects.using.return_value.filter.return_value.first.return_value = loja
        with override_settings(DATABASES={"default": {}, "loja_x": {}}):
            out, err = configurar_tenant_relatorio_publico(4)
        self.assertIs(out, loja)
        self.assertIsNone(err)
        _set_db.assert_called_once()


class CriarRelatorioComissaoSmokeTest(SimpleTestCase):
    @patch("crm_vendas.relatorio_comissao_workflow.montar_dados_oportunidades_snapshot", return_value=[])
    @patch("crm_vendas.relatorio_comissao_workflow.agregar_totais_oportunidades", return_value={"qtd": 0})
    @patch("crm_vendas.relatorio_comissao_workflow.queryset_oportunidades_comissao")
    @patch("crm_vendas.models.Vendedor")
    @patch("crm_vendas.models.Conta")
    def test_sem_vendas_retorna_erro(self, mock_conta, *_mocks):
        mock_conta.objects.filter.return_value.first.return_value = MagicMock(nome="EP")
        rel, err = criar_relatorio_comissao(1, 10, periodo_inicio=None, periodo_fim=None)
        self.assertIsNone(rel)
        self.assertIn("nenhuma venda", (err or "").lower())

    @patch("crm_vendas.relatorio_comissao_workflow.montar_dados_oportunidades_snapshot", return_value=[{"valor": 100}])
    @patch(
        "crm_vendas.relatorio_comissao_workflow.agregar_totais_oportunidades",
        return_value={"qtd": 1, "total_vendas": 1000, "total_comissao": 150},
    )
    @patch("crm_vendas.relatorio_comissao_workflow.queryset_oportunidades_comissao")
    @patch("crm_vendas.models_relatorio_comissao.RelatorioComissao")
    @patch("crm_vendas.models.Conta")
    def test_cria_relatorio_com_totais(self, mock_conta, mock_rc_cls, *_mocks):
        ep = MagicMock()
        ep.nome = "Empresa X"
        mock_conta.objects.filter.return_value.first.return_value = ep
        criado = MagicMock()
        mock_rc_cls.objects.create.return_value = criado

        rel, err = criar_relatorio_comissao(
            1, 10, periodo_descricao="Jun/2026",
            periodo_inicio=None, periodo_fim=None,
        )

        self.assertIs(rel, criado)
        self.assertIsNone(err)
        kwargs = mock_rc_cls.objects.create.call_args.kwargs
        self.assertEqual(kwargs["quantidade_vendas"], 1)
        self.assertEqual(kwargs["status"], "pendente_aprovacao")

    def test_empresa_prestadora_inexistente(self):
        with patch("crm_vendas.models.Conta") as mock_conta:
            mock_conta.objects.filter.return_value.first.return_value = None
            rel, err = criar_relatorio_comissao(1, 999)
        self.assertIsNone(rel)
        self.assertIn("prestadora", (err or "").lower())
