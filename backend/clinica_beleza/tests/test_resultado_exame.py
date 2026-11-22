"""Sugestão de resultado de exame por sexo, idade e texto do laudo."""
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from clinica_beleza.exame_referencia import classificar_valor, idade_em_anos, resolver_faixa_catalogo
from clinica_beleza.resultado_exame_service import (
    extrair_marcadores_do_texto,
    montar_sugestao,
)


class ExameReferenciaTest(SimpleTestCase):
    def test_idade_e_sexo_mudam_faixa_de_hemoglobina(self):
        mulher = resolver_faixa_catalogo("hemoglobina", sexo="F", idade=30)
        homem = resolver_faixa_catalogo("hemoglobina", sexo="M", idade=30)
        crianca = resolver_faixa_catalogo("hemoglobina", sexo="F", idade=8)
        self.assertEqual(mulher["min"], 12.0)
        self.assertEqual(homem["min"], 13.0)
        self.assertEqual(crianca["max"], 14.5)

    def test_classifica_alto_baixo_dentro(self):
        self.assertEqual(classificar_valor(10.0, 12.0, 16.0), "baixo")
        self.assertEqual(classificar_valor(14.0, 12.0, 16.0), "dentro")
        self.assertEqual(classificar_valor(18.0, 12.0, 16.0), "alto")

    def test_idade_em_anos(self):
        self.assertEqual(idade_em_anos(date(2000, 1, 1), date(2026, 11, 22)), 26)


class ExtracaoESugestaoTest(SimpleTestCase):
    def test_extrai_glicose_e_tsh_do_texto(self):
        texto = "GLICOSE 95 mg/dL 70 a 99\nTSH 5,20 µUI/mL 0,40 - 4,00"
        marcadores = extrair_marcadores_do_texto(texto)
        codigos = {m["codigo"] for m in marcadores}
        self.assertIn("glicose", codigos)
        self.assertIn("tsh", codigos)
        glicose = next(m for m in marcadores if m["codigo"] == "glicose")
        self.assertEqual(glicose["valor"], 95.0)
        self.assertEqual(glicose["faixa_min"], 70.0)

    def test_sugestao_usa_sexo_do_cadastro(self):
        patient = SimpleNamespace(sexo="F", data_nascimento=date(1990, 5, 1))
        marcadores, texto, aviso = montar_sugestao(
            [{"codigo": "hemoglobina", "nome": "Hemoglobina", "valor": 11.5, "unidade": "g/dL"}],
            patient,
            date(2026, 11, 22),
        )
        self.assertEqual(marcadores[0]["status"], "baixo")
        self.assertIn("mulher", texto)
        self.assertFalse(aviso)

    def test_aviso_sem_sexo_nem_nascimento(self):
        patient = SimpleNamespace(sexo="", data_nascimento=None)
        _marcadores, texto, aviso = montar_sugestao(
            [{"codigo": "glicose", "nome": "Glicose", "valor": 90, "unidade": "mg/dL"}],
            patient,
            date(2026, 11, 22),
        )
        self.assertIn("sexo", aviso.lower())
        self.assertIn("nascimento", aviso.lower())
        self.assertIn("Sugestão", texto)


class ImportarPdfTest(SimpleTestCase):
    @patch("clinica_beleza.resultado_exame_service.salvar_pdf_pessoa", return_value="https://media.example/pdf.pdf")
    @patch("clinica_beleza.resultado_exame_service._texto_pdf", return_value="GLICOSE 110 mg/dL 70 a 99")
    @patch("clinica_beleza.resultado_exame_service.ResultadoExamePaciente.objects.create")
    def test_importar_grava_marcadores(self, mock_create, _texto, _salvar):
        from clinica_beleza.resultado_exame_service import importar_pdf_resultado

        criado = SimpleNamespace(id=1)
        mock_create.return_value = criado
        patient = SimpleNamespace(id=9, sexo="M", data_nascimento=date(1985, 1, 1), nome="PAC")
        consulta = SimpleNamespace(id=598, loja_id=6, patient=patient, patient_id=9)
        resultado = importar_pdf_resultado(consulta, arquivo_bytes=b"%PDF-1.4", nome_arquivo="laudo.pdf")
        self.assertIs(resultado, criado)
        kwargs = mock_create.call_args.kwargs
        self.assertEqual(kwargs["pdf_url"], "https://media.example/pdf.pdf")
        self.assertTrue(any(m["codigo"] == "glicose" and m["status"] == "alto" for m in kwargs["marcadores"]))
