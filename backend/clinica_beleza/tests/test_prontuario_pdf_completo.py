"""Regressão: PDF completo do prontuário (Imprimir Completo)."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.prontuario_pdf.generators import (
    gerar_pdf_prontuario_completo,
    gerar_pdf_secao,
)


class GerarPdfProntuarioCompletoTests(SimpleTestCase):
    @patch("clinica_beleza.prontuario_pdf.generators.Patient")
    def test_paciente_inexistente_levanta_value_error_nao_import_error(self, mock_patient):
        mock_patient.objects.filter.return_value.first.return_value = None
        with self.assertRaises(ValueError):
            gerar_pdf_prontuario_completo(1825)

    @patch("clinica_beleza.prontuario_pdf.generators._finalize_pdf_bytes", side_effect=lambda _loja, buf: buf)
    @patch("clinica_beleza.prontuario_pdf.generators._build_header_elements", return_value=[])
    @patch("clinica_beleza.prontuario_pdf.generators.get_top_margin", return_value=20)
    @patch("clinica_beleza.prontuario_pdf.generators.listar_prontuario_paciente")
    @patch("clinica_beleza.prontuario_pdf.generators.Patient")
    def test_completo_gera_pdf_sem_documentos(self, mock_patient, mock_listar, *_mocks):
        patient = MagicMock()
        patient.nome = "MARCIA BATAGLIA"
        patient.loja_id = 6
        mock_patient.objects.filter.return_value.first.return_value = patient
        mock_listar.return_value = {}

        buf = gerar_pdf_prontuario_completo(1825)
        pdf = buf.getvalue()

        self.assertTrue(pdf.startswith(b"%PDF-"))
        mock_listar.assert_called_once_with(1825)

    @patch("clinica_beleza.prontuario_pdf.generators.Patient")
    def test_secao_paciente_inexistente_nao_quebra_import(self, mock_patient):
        mock_patient.objects.filter.return_value.first.return_value = None
        with self.assertRaises(ValueError):
            gerar_pdf_secao(1825, "anamnese")
