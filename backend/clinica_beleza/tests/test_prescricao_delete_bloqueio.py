"""Regra: consulta finalizada não permite excluir a receita (só visualizar)."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from rest_framework import status


class PrescricaoDeleteBloqueioTest(SimpleTestCase):
    def _view(self):
        from clinica_beleza.views_consultas.prescricoes import ConsultaPrescricaoDeleteView

        return ConsultaPrescricaoDeleteView()

    @patch("clinica_beleza.views_consultas.prescricoes.remover_pdf_media_prescricao")
    @patch("clinica_beleza.views_consultas.prescricoes.PrescricaoMemed")
    def test_consulta_finalizada_bloqueia_exclusao(self, mock_model, mock_remover):
        consulta = SimpleNamespace(status="COMPLETED", data_fim=None, appointment=None)
        presc = MagicMock(consulta=consulta)
        mock_model.objects.select_related.return_value.get.return_value = presc

        resp = self._view().delete(MagicMock(), consulta_id=1, pk=1)

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        presc.delete.assert_not_called()
        mock_remover.assert_not_called()

    @patch("clinica_beleza.views_consultas.prescricoes.remover_pdf_media_prescricao")
    @patch("clinica_beleza.views_consultas.prescricoes.PrescricaoMemed")
    def test_consulta_em_andamento_permite_exclusao(self, mock_model, mock_remover):
        consulta = SimpleNamespace(status="IN_PROGRESS", data_fim=None, appointment=None)
        presc = MagicMock(consulta=consulta)
        mock_model.objects.select_related.return_value.get.return_value = presc

        resp = self._view().delete(MagicMock(), consulta_id=1, pk=1)

        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        presc.delete.assert_called_once()
        mock_remover.assert_called_once_with(presc)


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
