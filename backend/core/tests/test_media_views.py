from types import SimpleNamespace
from unittest.mock import patch

from django.db.utils import ProgrammingError
from django.test import SimpleTestCase

from core.media_views import _buscar_paciente_midia, _resolver_folder_upload


class ResolverFolderUploadTest(SimpleTestCase):
    def test_usa_nome_quando_tabela_da_estetica_nao_existe(self):
        request = SimpleNamespace(
            data={"folder": "fotos", "patient_id": "1", "patient_nome": "Mariela", "patient_cpf": "11540472299"}
        )
        with patch("core.media_views._buscar_paciente_midia", return_value=None):
            pasta = _resolver_folder_upload(request)
        self.assertTrue(pasta.endswith("/fotos"))
        self.assertIn("mariela", pasta)

    def test_buscar_paciente_sobrevive_tabela_ausente(self):
        with patch("clinica_beleza.models.Patient") as mock_patient:
            mock_patient.objects.filter.side_effect = ProgrammingError("clinica_beleza_patient")
            with patch("clinica_geral.models.Paciente") as mock_geral:
                mock_geral.objects.filter.return_value.first.return_value = SimpleNamespace(
                    nome="Mariela", cpf="11540472299", id=1
                )
                achado = _buscar_paciente_midia("1")
        self.assertEqual(achado.nome, "Mariela")

    def test_sem_paciente_fica_na_pasta_do_tipo(self):
        pasta = _resolver_folder_upload(SimpleNamespace(data={"folder": "docs"}))
        self.assertEqual(pasta, "docs")

    def test_docs_do_paciente_vao_para_pdf(self):
        request = SimpleNamespace(
            data={"folder": "docs", "patient_nome": "Marcia Bataglia", "patient_cpf": "12345678901"}
        )
        pasta = _resolver_folder_upload(request)
        self.assertEqual(pasta, "marcia-bataglia_12345678901/pdf")
