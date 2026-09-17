"""Testes: limpeza de PDF/fotos ao excluir consulta não finalizada."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.media_consulta_cleanup import _arquivo_pdf_da_consulta
from clinica_beleza.memed_prescricao_service import nome_arquivo_pdf_prescricao


class NomesPdfConsultaTests(SimpleTestCase):
    def test_nome_estavel_prescricao(self):
        self.assertEqual(
            nome_arquivo_pdf_prescricao("295237918", 16),
            "prescricao_295237918.pdf",
        )

    def test_arquivo_da_consulta_secao_e_termo(self):
        conhecidos = {"consulta_10_atendimento.pdf", "orcamento_3_"}
        self.assertTrue(
            _arquivo_pdf_da_consulta("consulta_10_produtos.pdf", 10, conhecidos),
        )
        self.assertTrue(
            _arquivo_pdf_da_consulta("termo_botox_10.pdf", 10, conhecidos),
        )
        self.assertTrue(
            _arquivo_pdf_da_consulta("orcamento_3_20260916.pdf", 10, conhecidos),
        )
        self.assertFalse(
            _arquivo_pdf_da_consulta("consulta_11_atendimento.pdf", 10, conhecidos),
        )
        self.assertFalse(
            _arquivo_pdf_da_consulta("prontuario_completo_5.pdf", 10, conhecidos),
        )


class LimparMidiaConsultaTests(SimpleTestCase):
    @patch("clinica_beleza.media_consulta_cleanup.media_delete_tenant", return_value=True)
    @patch("clinica_beleza.media_consulta_cleanup.media_list_files")
    @patch("clinica_beleza.media_consulta_cleanup.pasta_media_paciente", return_value="luis_id10")
    @patch("clinica_beleza.media_consulta_cleanup._tenant_loja", return_value="37302743000126")
    @patch("clinica_beleza.media_consulta_cleanup._paciente_consulta")
    @patch("clinica_beleza.media_consulta_cleanup.nomes_pdf_da_consulta")
    @patch("clinica_beleza.foto_paciente_service.limpar_fotos_media_da_consulta", return_value=2)
    def test_exclui_fotos_pdfs_e_prescricoes(
        self,
        mock_fotos,
        mock_nomes,
        mock_paciente,
        _tenant,
        _pasta,
        mock_list,
        mock_delete,
    ):
        from clinica_beleza.media_consulta_cleanup import limpar_midia_da_consulta

        consulta = SimpleNamespace(pk=10, loja_id=7, patient=MagicMock())
        mock_paciente.return_value = consulta.patient
        mock_nomes.return_value = {
            "consulta_10_atendimento.pdf",
            "prescricao_295237918.pdf",
            "orcamento_3_",
        }
        mock_list.return_value = {
            "files": [
                {"filename": "consulta_10_atendimento.pdf"},
                {"filename": "termo_peeling_10.pdf"},
                {"filename": "prontuario_completo_5.pdf"},
            ],
        }
        presc_qs = MagicMock()

        with patch(
            "clinica_beleza.models.PrescricaoMemed.objects",
        ) as presc_objects:
            presc_objects.filter.return_value = presc_qs
            n = limpar_midia_da_consulta(consulta)

        self.assertEqual(n, 5)  # 2 fotos + atendimento + prescricao + termo
        mock_fotos.assert_called_once_with(consulta)
        apagados = {c.args[1] for c in mock_delete.call_args_list}
        self.assertIn("consulta_10_atendimento.pdf", apagados)
        self.assertIn("termo_peeling_10.pdf", apagados)
        self.assertIn("prescricao_295237918.pdf", apagados)
        self.assertNotIn("prontuario_completo_5.pdf", apagados)
        presc_objects.filter.assert_called_with(consulta_id=10)
        presc_qs.delete.assert_called_once()
