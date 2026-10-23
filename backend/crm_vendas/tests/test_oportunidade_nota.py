"""Testes unitários para OportunidadeNotaViewSet e OportunidadeNota.
"""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase


class OportunidadeNotaModelTests(SimpleTestCase):
    """Testa comportamentos do model OportunidadeNota."""

    def test_imutabilidade_http_methods(self):
        """ViewSet não deve aceitar PUT/PATCH/DELETE (append-only)."""
        from crm_vendas.views_pipelines import OportunidadeNotaViewSet
        allowed = OportunidadeNotaViewSet.http_method_names
        self.assertIn("get", allowed)
        self.assertIn("post", allowed)
        self.assertNotIn("put", allowed)
        self.assertNotIn("patch", allowed)
        self.assertNotIn("delete", allowed)

    def test_ordering_cronologico(self):
        """Notas devem ser ordenadas por created_at ASC (histórico cronológico)."""
        from crm_vendas.models.oportunidade_notas import OportunidadeNota
        ordering = OportunidadeNota._meta.ordering
        self.assertEqual(ordering, ["created_at"])

    def test_tipo_choices(self):
        """Tipos válidos: resposta_cliente e nota_interna."""
        from crm_vendas.models.oportunidade_notas import OportunidadeNota
        tipos = [t[0] for t in OportunidadeNota.TIPO_CHOICES]
        self.assertIn("resposta_cliente", tipos)
        self.assertIn("nota_interna", tipos)

    def test_indexes_presentes(self):
        """Deve ter índices em (loja_id, oportunidade) e (loja_id, created_at)."""
        from crm_vendas.models.oportunidade_notas import OportunidadeNota
        idx_names = [idx.name for idx in OportunidadeNota._meta.indexes]
        self.assertIn("crm_opor_nota_loja_op_idx", idx_names)
        self.assertIn("crm_opor_nota_loja_dt_idx", idx_names)


class OportunidadeNotaPerformCreateTests(SimpleTestCase):
    """Testa que perform_create injeta autor_nome corretamente."""

    def _make_request(self, user_display=None, vendedor_nome=None):
        req = MagicMock()
        req.user = MagicMock()
        req.user.get_full_name.return_value = user_display or ""
        req.user.username = "user_test"
        return req

    @patch("crm_vendas.views_pipelines.get_current_vendedor_id", return_value=None)
    @patch("crm_vendas.views_pipelines.OportunidadeNota.objects")
    def test_autor_nome_usa_display_name_do_owner(self, mock_obj, *_):
        """Owner: autor_nome deve ser o full_name do user."""
        from crm_vendas.views_pipelines import _autor_nome_negociacao

        req = self._make_request(user_display="Felix Owner")
        autor = _autor_nome_negociacao(req)
        self.assertEqual(autor, "Felix Owner")

    @patch("crm_vendas.views_pipelines.get_current_vendedor_id", return_value=42)
    def test_autor_nome_usa_vendedor_quando_logado(self, *_):
        """Vendedor: autor_nome deve ser o nome do vendedor."""
        from crm_vendas.views_pipelines import _autor_nome_negociacao

        req = MagicMock()
        req.user = MagicMock()

        with patch("crm_vendas.views_pipelines.Vendedor") as mock_vend:
            vend_inst = MagicMock()
            vend_inst.nome = "João Vendedor"
            mock_vend.objects.filter.return_value.only.return_value.first.return_value = vend_inst
            autor = _autor_nome_negociacao(req)
            self.assertEqual(autor, "João Vendedor")

    def test_autor_nome_fallback_para_username(self):
        """Sem full_name, usa username."""
        from crm_vendas.views_pipelines import _autor_nome_negociacao

        with patch("crm_vendas.views_pipelines.get_current_vendedor_id", return_value=None):
            req = MagicMock()
            req.user = MagicMock()
            req.user.get_full_name.return_value = ""
            req.user.username = "felix_user"
            autor = _autor_nome_negociacao(req)
            self.assertEqual(autor, "felix_user")


class OportunidadeNotaVisibilidadeTests(SimpleTestCase):
    """O histórico da oportunidade é da venda, não do vendedor dono do card."""

    def _view(self, params):
        from crm_vendas.views_pipelines import OportunidadeNotaViewSet

        view = OportunidadeNotaViewSet()
        view.request = MagicMock()
        view.request.query_params = params
        return view

    def test_vendedor_ve_todas_as_notas_da_oportunidade(self):
        qs = MagicMock()
        result = self._view({"oportunidade_id": "10"}).filter_by_vendedor(qs)
        self.assertIs(result, qs)
        qs.filter.assert_not_called()

    @patch("crm_vendas.mixins.VendedorFilterMixin.filter_by_vendedor")
    def test_lista_sem_oportunidade_continua_no_vendedor(self, mock_filtro):
        qs = MagicMock()
        mock_filtro.return_value = qs
        result = self._view({}).filter_by_vendedor(qs)
        self.assertIs(result, qs)
        mock_filtro.assert_called_once()


class VendaGanhaNaoExcluiTests(SimpleTestCase):
    def test_closed_won_recusa_exclusao(self):
        from crm_vendas.views_pipelines import OportunidadeViewSet

        view = OportunidadeViewSet()
        view.request = MagicMock()
        oportunidade = MagicMock()
        oportunidade.etapa = "closed_won"
        view.get_object = MagicMock(return_value=oportunidade)

        response = view.destroy(view.request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("Venda ganha", response.data["detail"])

    @patch("crm_vendas.mixins.CRMSchemaRecoveryMixin.destroy")
    def test_outra_etapa_segue_a_exclusao(self, mock_destroy):
        from crm_vendas.views_pipelines import OportunidadeViewSet

        view = OportunidadeViewSet()
        view.request = MagicMock()
        oportunidade = MagicMock()
        oportunidade.etapa = "proposal"
        view.get_object = MagicMock(return_value=oportunidade)
        mock_destroy.return_value = MagicMock(status_code=204)

        response = view.destroy(view.request)

        self.assertEqual(response.status_code, 204)
        mock_destroy.assert_called_once()


class HistoricoPdfCabecalhoTests(SimpleTestCase):
    def _oportunidade(self):
        from datetime import date, datetime, timezone
        from types import SimpleNamespace

        nota = SimpleNamespace(
            created_at=datetime(2026, 10, 22, 20, 23, tzinfo=timezone.utc),
            tipo="resposta_cliente",
            autor_nome="FELIPE COSTA FELIX",
            texto="Cliente não respondeu à mensagem do controle de qualidade.",
        )
        lead = SimpleNamespace(
            nome="JAYME DANIEL SILVA MORHEB",
            empresa="MORHEB SERVICOS MEDICOS LTDA",
            telefone="86999999999",
            contato=None,
            conta_id=None,
            conta=None,
            cpf_cnpj="12345678000199",
        )
        prestadora = SimpleNamespace(
            nome="ULTRASIS",
            razao_social="ULTRASIS INFORMATICA LTDA",
            cnpj="00000000000191",
            logo="https://media.example/ultrasys.png",
        )
        return SimpleNamespace(
            lead=lead,
            valor=440,
            etapa="closed_won",
            vendedor=SimpleNamespace(nome="LUIZ HENRIQUE FELIX"),
            empresa_prestadora=prestadora,
            data_fechamento_ganho=date(2026, 9, 14),
            data_fechamento=None,
            feedback_pos_venda="",
            motivo_perda="",
            notas_negociacao=SimpleNamespace(all=lambda: [nota]),
        )

    @patch("crm_vendas.pdf_proposta_contrato.sections._build_cabecalho")
    def test_pdf_usa_logo_da_loja_e_da_prestadora(self, mock_cabecalho):
        from crm_vendas.relatorios_negociacao_pdf import gerar_pdf_historico_oportunidade
        from types import SimpleNamespace

        loja = SimpleNamespace(logo="https://media.example/felix.png", login_logo="")
        pdf = gerar_pdf_historico_oportunidade(self._oportunidade(), loja)

        self.assertTrue(pdf.startswith(b"%PDF"))
        args = mock_cabecalho.call_args.args
        self.assertEqual(args[1], "https://media.example/felix.png")
        self.assertEqual(args[2], "HISTÓRICO DE NEGOCIAÇÃO")
        self.assertEqual(args[3], "https://media.example/ultrasys.png")
