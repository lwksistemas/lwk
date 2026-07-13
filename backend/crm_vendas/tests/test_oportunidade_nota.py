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
