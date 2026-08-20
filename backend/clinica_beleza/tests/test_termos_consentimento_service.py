"""Testes do serviço de TCLE Interativo."""
from django.test import SimpleTestCase

from clinica_beleza.termos_consentimento_service import (
    nome_sem_anadem,
    normalizar_secoes,
    validar_respostas_interativo,
)


class NomeSemAnademTest(SimpleTestCase):
    def test_remove_marca(self):
        self.assertEqual(nome_sem_anadem("TCLE ANADEM Microagulhamento"), "TCLE Microagulhamento")

    def test_vazio_vira_rotulo_padrao(self):
        self.assertEqual(nome_sem_anadem("ANADEM"), "TCLE Interativo")


class ValidarRespostasTest(SimpleTestCase):
    def test_exige_sim_na_leitura(self):
        secoes = [{"id": "a", "titulo": "Indicação", "tipo": "sim_nao", "codigo": "I", "texto": ""}]
        self.assertIsNotNone(validar_respostas_interativo(secoes, {}))
        self.assertIsNotNone(validar_respostas_interativo(secoes, {"a": {"sim_nao": "nao"}}))
        self.assertIsNone(validar_respostas_interativo(secoes, {"a": {"sim_nao": "sim"}}))

    def test_consinto_obrigatorio(self):
        secoes = [{"id": "z", "titulo": "Final", "tipo": "consinto", "codigo": "", "texto": ""}]
        self.assertIsNotNone(validar_respostas_interativo(secoes, {"z": {"consinto": "recuso"}}))
        self.assertIsNone(validar_respostas_interativo(secoes, {"z": {"consinto": "consinto"}}))

    def test_gravidez_exige_sim_nao(self):
        secoes = [{"id": "g", "titulo": "Gravidez", "tipo": "gravidez", "codigo": "", "texto": ""}]
        self.assertIsNotNone(validar_respostas_interativo(secoes, {}))
        self.assertIsNone(validar_respostas_interativo(secoes, {"g": {"sim_nao": "nao"}}))

    def test_normaliza_id(self):
        secoes = normalizar_secoes([{"titulo": "X", "tipo": "sim_nao", "texto": "oi"}])
        self.assertEqual(len(secoes), 1)
        self.assertTrue(secoes[0]["id"])
