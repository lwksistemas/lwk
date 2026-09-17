"""Regra: consulta finalizada não permite excluir a receita (só visualizar)."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from rest_framework import status


class PrescricaoDeleteBloqueioTest(SimpleTestCase):
    def _view(self):
        from clinica_beleza.views_consultas.prescricoes import ConsultaPrescricaoDeleteView

        return ConsultaPrescricaoDeleteView()

    def _presc(self, status):
        consulta = SimpleNamespace(status=status, data_fim=None, appointment=None)
        return MagicMock(consulta=consulta, consulta_id=1)

    @patch("clinica_beleza.views_consultas.prescricoes.remover_pdf_media_prescricao")
    def test_consulta_finalizada_bloqueia_exclusao(self, mock_remover):
        presc = self._presc("COMPLETED")
        view = self._view()
        view.get_object = MagicMock(return_value=presc)

        resp = view.delete(MagicMock(), consulta_id=1, pk=1)

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        presc.delete.assert_not_called()
        mock_remover.assert_not_called()

    @patch("clinica_beleza.views_consultas.prescricoes.remover_pdf_media_prescricao")
    def test_consulta_em_andamento_permite_exclusao(self, mock_remover):
        presc = self._presc("IN_PROGRESS")
        view = self._view()
        view.get_object = MagicMock(return_value=presc)

        resp = view.delete(MagicMock(), consulta_id=1, pk=1)

        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        presc.delete.assert_called_once()
        mock_remover.assert_called_once_with(presc)


class PrescricaoPdfSubstituiFallbackTest(SimpleTestCase):
    def _view(self):
        from clinica_beleza.views_consultas.prescricoes import PrescricaoMemedPdfView

        return PrescricaoMemedPdfView()

    @patch("clinica_beleza.memed_prescricao_service.resolver_pdf_prescricao")
    @patch("clinica_beleza.views_consultas.prescricoes.PrescricaoMemed")
    @patch("superadmin.models.Loja")
    def test_pdf_assinado_substitui_url_local(self, mock_loja, mock_model, mock_resolver):
        presc = MagicMock()
        presc.loja_id = 6
        presc.prescricao_id = "295237918"
        presc.pdf_url = "https://media.lwksistemas.com.br/files/x/local.pdf"
        presc.professional = MagicMock()
        presc.patient = MagicMock()
        presc.consulta_id = 153
        mock_model.objects.select_related.return_value.get.return_value = presc
        mock_loja.objects.using.return_value.filter.return_value.first.return_value = MagicMock()
        mock_resolver.return_value = "https://media.lwksistemas.com.br/files/x/memed.pdf"

        resp = self._view().post(MagicMock(), pk=16)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["pdf_url"], "https://media.lwksistemas.com.br/files/x/memed.pdf")
        presc.save.assert_called_once()
        mock_resolver.assert_called_once()

    @patch("clinica_beleza.memed_prescricao_service.resolver_pdf_prescricao")
    @patch("clinica_beleza.views_consultas.prescricoes.PrescricaoMemed")
    @patch("superadmin.models.Loja")
    @patch(
        "clinica_beleza.memed_prescricao_service.pdf_midia_estavel",
        return_value=True,
    )
    def test_pdf_estavel_nao_grava_de_novo(self, mock_estavel, mock_loja, mock_model, mock_resolver):
        presc = MagicMock()
        presc.pk = 16
        presc.loja_id = 6
        presc.prescricao_id = "295237918"
        presc.pdf_url = (
            "https://media.lwksistemas.com.br/files/x/paciente/pdf/prescricao_295237918.pdf"
        )
        presc.professional = MagicMock()
        presc.patient = MagicMock()
        presc.consulta_id = 153
        mock_model.objects.select_related.return_value.get.return_value = presc
        mock_loja.objects.using.return_value.filter.return_value.first.return_value = MagicMock()

        resp = self._view().post(MagicMock(), pk=16)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["pdf_url"], presc.pdf_url)
        mock_resolver.assert_not_called()
        presc.save.assert_not_called()
        mock_estavel.assert_called()


class FotoDeleteBloqueioTest(SimpleTestCase):
    def test_consulta_finalizada_bloqueia_exclusao_foto(self):
        # _consulta_permite_envio_foto retorna erro (bloqueio) p/ status != IN_PROGRESS/RECEBER
        from clinica_beleza.views_foto_paciente import _consulta_permite_envio_foto

        consulta = SimpleNamespace(status="COMPLETED", loja_id=1)
        with patch("superadmin.plano_features.loja_plano_permite_fotos", return_value=(True, None)):
            resp = _consulta_permite_envio_foto(consulta)
        self.assertIsNotNone(resp)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_consulta_em_andamento_permite_foto(self):
        from clinica_beleza.views_foto_paciente import _consulta_permite_envio_foto

        consulta = SimpleNamespace(status="IN_PROGRESS", loja_id=1)
        with patch("superadmin.plano_features.loja_plano_permite_fotos", return_value=(True, None)):
            resp = _consulta_permite_envio_foto(consulta)
        self.assertIsNone(resp)
