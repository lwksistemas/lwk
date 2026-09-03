from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from core.media_storage import (
    destino_midia_paciente_legado,
    folder_media_paciente,
    pasta_media_paciente,
    tipo_pasta_paciente,
)


class PastaMediaPacienteTest(TestCase):
    def test_usa_cpf_quando_existe(self):
        pessoa = SimpleNamespace(nome="Luiz Henrique Felix", cpf="222.392.558-89", id=1)
        self.assertEqual(pasta_media_paciente(pessoa), "luiz-henrique-felix_22239255889")

    def test_crm_usa_cpf_cnpj(self):
        lead = SimpleNamespace(nome="Felix Representacoes", cpf_cnpj="41.449.198/0001-72", id=9)
        self.assertEqual(pasta_media_paciente(lead), "felix-representacoes_41449198000172")

    def test_sem_cpf_usa_id(self):
        pessoa = SimpleNamespace(nome="Lidiane Campos", cpf="", id=2109)
        self.assertEqual(pasta_media_paciente(pessoa), "lidiane-campos_id2109")


class FolderMediaPacienteTest(TestCase):
    def test_fotos_ficam_dentro_do_paciente(self):
        pessoa = SimpleNamespace(nome="Bianca", cpf="46373544800", id=2)
        self.assertEqual(folder_media_paciente("fotos", pessoa), "bianca_46373544800/fotos")

    def test_docs_e_receitas_viram_pdf(self):
        pessoa = SimpleNamespace(nome="Marcia", cpf="", id=1825)
        self.assertEqual(folder_media_paciente("docs", pessoa), "marcia_id1825/pdf")
        self.assertEqual(folder_media_paciente("pdf", pessoa), "marcia_id1825/pdf")
        self.assertEqual(tipo_pasta_paciente("recibos"), "pdf")

    def test_sem_paciente_mantem_tipo(self):
        self.assertEqual(folder_media_paciente("avatars", None), "avatars")
        self.assertEqual(folder_media_paciente("docs", None), "pdf")


class DestinoMidiaLegadoTest(TestCase):
    def test_fotos_paciente_viram_paciente_fotos(self):
        self.assertEqual(
            destino_midia_paciente_legado("fotos/luiz-henrique-felix_22239255889"),
            "luiz-henrique-felix_22239255889/fotos",
        )

    def test_docs_viram_paciente_pdf(self):
        self.assertEqual(
            destino_midia_paciente_legado("docs/marcia-bataglia_id1825"),
            "marcia-bataglia_id1825/pdf",
        )

    def test_nao_mexe_no_formato_novo_nem_admin(self):
        self.assertIsNone(destino_midia_paciente_legado("luiz-henrique-felix_22239255889/fotos"))
        self.assertIsNone(destino_midia_paciente_legado("admin/fotos"))
        self.assertIsNone(destino_midia_paciente_legado("fotos"))


class SalvarPdfPacienteTest(TestCase):
    @patch("clinica_beleza.media_docs_service.media_upload_tenant", return_value="https://media.example/x.pdf")
    @patch("clinica_beleza.media_docs_service._resolver_tenant_loja", return_value="37302743000126")
    def test_grava_em_paciente_pdf(self, _tenant, mock_upload):
        from clinica_beleza.media_docs_service import salvar_pdf_paciente

        patient = SimpleNamespace(nome="Renata Ribeiro", cpf="", id=2231)
        url = salvar_pdf_paciente(1, patient, b"%PDF-1.4", "receita.pdf")
        self.assertEqual(url, "https://media.example/x.pdf")
        mock_upload.assert_called_once()
        kwargs = mock_upload.call_args.kwargs
        self.assertEqual(kwargs["folder"], "renata-ribeiro_id2231/pdf")
        self.assertEqual(kwargs["filename"], "receita.pdf")
