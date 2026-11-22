"""Sugestão de resultado de exame por sexo, idade e texto do laudo."""
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from clinica_beleza.exame_comparacao import comparar_marcadores
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


LAUDO_HAPVIDA_AMOSTRA = """
GLICOSE
Resultado: 97.9 mg/dL                                                                 65 - 100 mg/dL
LIPIDOGRAMA
Resultado: Colesterol Total....: 166 mg/dL
           Colesterol HDL......: 34 mg/dL
           Colesterol LDL......: 109 mg/dL
           Triglicérides.......: 121 mg/dL
           Colesterol VLDL.....: 24 mg/dL
Adulto......: Colesterol Total (com ou sem jejum): Inferior a 190 mg/dL
HEMOGLOBINA GLICADA
Resultado: 5.33 %
Glicose Média Estimada: 106 mg/dL
HEMOGRAMA COMPLETO
Eritrócitos...:                             5.29 10¹²/L                                                            4.5 - 5.5 10¹²/L
Hemoglobina...:                             16.0 g/dL                                                              13 - 17 g/dL
Hematócrito...:                             45.8 %                                                                 40 - 50 %
VCM...........:                             86.6 fL                                                                83 - 101 fL
HCM...........:                             30.2 pg                                                                27 - 31 pg
CHCM..........:                             34.9 g/dL                                                              31.5 - 34.5 g/dL
RDW...........:                             12.7 %                                                                 11.6 - 14 %
Leucócitos....:                       5710 /mm³                             4000 - 10000 /mm³
Segmentados...:         58 %             3312 /mm³                          48 à 73%
Eosinófilos...:         1 %              57 /mm³                            1 à 6%
Basófilos.....:         0 %              0 /mm³                             0 à 2%
Linf. Típicos:          32 %             1827 /mm³                          27 à 42%
Monócitos.....:         9 %              514 /mm³                           2 à 12%
Plaquetas.....:                  192000 /mm³                                                                       150000 - 400000 /mm³
VITAMINA B12
Resultado: 201 pg/mL                                                                                             211 - 911 pg/mL
FERRITINA
Resultado: 349,3 ng/mL                                                                                           Homens..: 22,0 - 322,0 ng/mL
ANTÍGENO PROSTÁTICO ESPECÍFICO - PSA TOTAL
Resultado: 0.91 ng/mL                                                                                            Até 4.00 ng/mL
ANTÍGENO PROSTÁTICO ESPECÍFICO - PSA LIVRE
Resultado: 0.24 ng/mL                                                                                     Inferior a 0,90 ng/mL
TESTOSTERONA LIVRE
SHBG..............: 41,30 mmol/L
Testosterona Livre: 5,564 ng/dL
TESTOSTERONA TOTAL
Resultado: 320,4 ng/dL                                                                                           Homens abaixo de 50 anos..: 197,5 a 669,5 ng/dL
VITAMINA D - 25 OH
Resultado: 25.4 ng/mL                                                                      Desejável (até 60 anos).....: Superior a 20 ng/mL
"""


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

    def test_extrai_laudo_hapvida_completo(self):
        marcadores = extrair_marcadores_do_texto(LAUDO_HAPVIDA_AMOSTRA)
        por_codigo = {m["codigo"]: m for m in marcadores}
        esperados = {
            "glicose": 97.9,
            "colesterol_total": 166.0,
            "hdl": 34.0,
            "ldl": 109.0,
            "triglicerides": 121.0,
            "vldl": 24.0,
            "hba1c": 5.33,
            "eritrocitos": 5.29,
            "hemoglobina": 16.0,
            "hematocrito": 45.8,
            "vcm": 86.6,
            "hcm": 30.2,
            "chcm": 34.9,
            "rdw": 12.7,
            "leucocitos": 5710.0,
            "plaquetas": 192000.0,
            "segmentados": 58.0,
            "linfocitos": 32.0,
            "monocitos": 9.0,
            "eosinofilos": 1.0,
            "basofilos": 0.0,
            "vitamina_b12": 201.0,
            "ferritina": 349.3,
            "psa_total": 0.91,
            "psa_livre": 0.24,
            "shbg": 41.3,
            "testosterona_livre": 5.564,
            "testosterona_total": 320.4,
            "vitamina_d": 25.4,
        }
        faltando = [c for c in esperados if c not in por_codigo]
        self.assertFalse(faltando, f"Marcadores faltando: {faltando}")
        for codigo, valor in esperados.items():
            self.assertAlmostEqual(por_codigo[codigo]["valor"], valor, places=2, msg=codigo)
        # Não deve pegar a glicose média estimada (106) no lugar da glicose
        self.assertAlmostEqual(por_codigo["glicose"]["valor"], 97.9, places=1)
        # Hemoglobina não deve ser a HbA1c
        self.assertAlmostEqual(por_codigo["hemoglobina"]["valor"], 16.0, places=1)
        self.assertEqual(por_codigo["leucocitos"]["faixa_max"], 10000.0)
        self.assertEqual(por_codigo["plaquetas"]["faixa_max"], 400000.0)
        # Não deve usar "0 a 09 anos" como faixa de colesterol
        self.assertGreater(por_codigo["colesterol_total"].get("faixa_max") or 0, 20)

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

    def test_apoio_so_fora_da_faixa(self):
        patient = SimpleNamespace(sexo="M", data_nascimento=date(1982, 6, 25))
        marcadores, texto, _aviso = montar_sugestao(
            [
                {"codigo": "hdl", "nome": "HDL colesterol", "valor": 34, "unidade": "mg/dL"},
                {"codigo": "colesterol_total", "nome": "Colesterol total", "valor": 166, "unidade": "mg/dL"},
            ],
            patient,
            date(2026, 11, 22),
        )
        por = {m["codigo"]: m for m in marcadores}
        self.assertEqual(por["hdl"]["status"], "baixo")
        self.assertTrue(por["hdl"]["sintomas_possiveis"])
        self.assertTrue(por["hdl"]["recomendacoes"])
        self.assertEqual(por["hdl"]["origem_apoio"], "catalogo")
        self.assertEqual(por["colesterol_total"]["status"], "dentro")
        self.assertEqual(por["colesterol_total"]["sintomas_possiveis"], [])
        self.assertEqual(por["colesterol_total"]["recomendacoes"], [])
        self.assertIn("Sintomas possíveis", texto)
        self.assertIn("Recomendações", texto)

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


class ComparacaoLaudosTest(SimpleTestCase):
    def test_compara_hdl_melhorou_e_ldl_piorou(self):
        anterior = [
            {"codigo": "hdl", "nome": "HDL", "valor": 34, "unidade": "mg/dL", "status": "baixo"},
            {"codigo": "ldl", "nome": "LDL", "valor": 109, "unidade": "mg/dL", "status": "alto"},
        ]
        atual = [
            {"codigo": "hdl", "nome": "HDL", "valor": 42, "unidade": "mg/dL", "status": "dentro"},
            {"codigo": "ldl", "nome": "LDL", "valor": 118, "unidade": "mg/dL", "status": "alto"},
            {"codigo": "glicose", "nome": "Glicose", "valor": 90, "unidade": "mg/dL", "status": "dentro"},
        ]
        comp = comparar_marcadores(atual, anterior, data_atual=date(2026, 11, 22), data_anterior=date(2026, 5, 10))
        por = {i["codigo"]: i for i in comp["itens"]}
        self.assertEqual(set(por), {"hdl", "ldl"})
        self.assertEqual(por["hdl"]["evolucao"], "melhorou")
        self.assertEqual(por["ldl"]["evolucao"], "piorou")
        self.assertEqual(comp["resumo"]["melhoraram"], 1)
        self.assertEqual(comp["resumo"]["pioraram"], 1)
        self.assertIn("Comparação", comp["texto"])

    def test_sem_marcadores_comuns(self):
        comp = comparar_marcadores(
            [{"codigo": "hdl", "nome": "HDL", "valor": 40, "status": "dentro"}],
            [{"codigo": "glicose", "nome": "Glicose", "valor": 90, "status": "dentro"}],
        )
        self.assertEqual(comp["itens"], [])
        self.assertIn("comum", comp["texto"].lower())


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
