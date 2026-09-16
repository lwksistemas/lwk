"""Status ACEITO/RECUSADO e mixin das views de orçamento."""
from unittest.mock import MagicMock

from django.test import SimpleTestCase

from clinica_beleza.orcamento_service import atualizar_status_orcamento, excluir_orcamento
from clinica_beleza.views_agenda import AgendaUpdateView
from clinica_beleza.views_base import GetObjectMixin
from clinica_beleza.views_consultas.prescricoes import ConsultaPrescricaoDeleteView
from clinica_beleza.views_consultas.procedimentos import ConsultaProcedimentoDetailView
from clinica_beleza.views_consultas.produtos import ConsultaProdutoDetailView
from clinica_beleza.views_orcamento import (
    OrcamentoDetalheView,
    OrcamentoEnviarView,
    OrcamentoPDFView,
)


class TestAtualizarStatusOrcamento(SimpleTestCase):
    def test_rascunho_para_aceito(self):
        orc = MagicMock(status="RASCUNHO")
        atualizar_status_orcamento(orc, "ACEITO")
        self.assertEqual(orc.status, "ACEITO")
        orc.save.assert_called_once_with(update_fields=["status", "updated_at"])

    def test_enviado_para_recusado(self):
        orc = MagicMock(status="ENVIADO")
        atualizar_status_orcamento(orc, "recusado")
        self.assertEqual(orc.status, "RECUSADO")

    def test_aceito_para_recusado(self):
        orc = MagicMock(status="ACEITO")
        atualizar_status_orcamento(orc, "RECUSADO")
        self.assertEqual(orc.status, "RECUSADO")

    def test_idempotente(self):
        orc = MagicMock(status="ACEITO")
        atualizar_status_orcamento(orc, "ACEITO")
        orc.save.assert_not_called()

    def test_rejeita_enviado_via_patch(self):
        orc = MagicMock(status="RASCUNHO")
        with self.assertRaises(ValueError):
            atualizar_status_orcamento(orc, "ENVIADO")

    def test_nao_exclui_aceito(self):
        orc = MagicMock(status="ACEITO")
        with self.assertRaises(ValueError):
            excluir_orcamento(orc)
        orc.delete.assert_not_called()

    def test_exclui_rascunho(self):
        orc = MagicMock(status="RASCUNHO")
        excluir_orcamento(orc)
        orc.delete.assert_called_once()


class TestOrcamentoViewsMixin(SimpleTestCase):
    def test_detalhe_pdf_enviar_usam_mixin(self):
        for view in (OrcamentoDetalheView, OrcamentoPDFView, OrcamentoEnviarView):
            self.assertTrue(issubclass(view, GetObjectMixin))
            self.assertEqual(view.not_found_message, "Orçamento não encontrado")

    def test_higiene_mixin_nas_demais_views(self):
        self.assertTrue(issubclass(AgendaUpdateView, GetObjectMixin))
        self.assertTrue(issubclass(ConsultaProdutoDetailView, GetObjectMixin))
        self.assertTrue(issubclass(ConsultaProcedimentoDetailView, GetObjectMixin))
        self.assertTrue(issubclass(ConsultaPrescricaoDeleteView, GetObjectMixin))

    def test_patch_aceita_status(self):
        orc = MagicMock(id=9, status="ENVIADO")
        view = OrcamentoDetalheView()
        view.get_object = MagicMock(return_value=orc)
        request = MagicMock()
        request.data = {"status": "ACEITO"}
        resp = view.patch(request, orcamento_id=9)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["status"], "ACEITO")
