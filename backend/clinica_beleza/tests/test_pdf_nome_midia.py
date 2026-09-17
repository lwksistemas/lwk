"""Nome estável de PDF a partir do texto (consulta, prontuário, Memed)."""
from django.test import SimpleTestCase

from clinica_beleza.pdf_nome_midia import (
    eh_pdf_memed,
    nome_estavel_do_texto,
    nome_pdf_consulta_do_texto,
    precisa_renomear_pdf,
)


class PrecisaRenomearPdfTests(SimpleTestCase):
    def test_uuid_e_generico(self):
        self.assertTrue(precisa_renomear_pdf("83df01b7b0b94d40a0f51c9db15fab54.pdf"))
        self.assertTrue(precisa_renomear_pdf("prescricao.pdf"))
        self.assertFalse(precisa_renomear_pdf("consulta_10_atendimento.pdf"))
        self.assertFalse(precisa_renomear_pdf("prescricao_295237918.pdf"))


class NomePdfConsultaTextoTests(SimpleTestCase):
    def test_secao_atendimento(self):
        texto = "Atendimento\nPaciente: LUIS\nConsulta: #10\nNotas do atendimento\n"
        self.assertEqual(nome_pdf_consulta_do_texto(texto), "consulta_10_atendimento.pdf")

    def test_secao_produtos(self):
        texto = "Produtos utilizados\nConsulta: #22\n"
        self.assertEqual(nome_pdf_consulta_do_texto(texto), "consulta_22_produtos.pdf")


class NomeEstavelTextoTests(SimpleTestCase):
    def test_prontuario_completo(self):
        self.assertEqual(
            nome_estavel_do_texto("Prontuário Completo — Ana", patient_id=5),
            "prontuario_completo_5.pdf",
        )

    def test_memed_com_um_id(self):
        texto = "https://validador.memed.com.br | Token: abc\nMEMED - Acesso à sua receita"
        self.assertTrue(eh_pdf_memed(texto))
        self.assertEqual(
            nome_estavel_do_texto(texto, prescricao_ids=["295237918"]),
            "prescricao_295237918.pdf",
        )

    def test_memed_sem_id_unico_nao_chuta(self):
        texto = "validador.memed.com.br"
        self.assertIsNone(nome_estavel_do_texto(texto, prescricao_ids=["1", "2"]))
