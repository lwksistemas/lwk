"""Testes do serviço de TCLE Interativo."""
from types import SimpleNamespace

from django.test import SimpleTestCase

from clinica_beleza.consentimento_service import consulta_exige_termo_listagem
from clinica_beleza.termos_consentimento_service import (
    nome_sem_anadem,
    normalizar_secoes,
    validar_respostas_interativo,
)


class TermoNaListaTest(SimpleTestCase):
    def test_procedimento_com_termo_aparece_na_lista(self):
        proc = SimpleNamespace(
            id=1,
            termo_consentimento_ativo=True,
            termo_template_id=None,
            termo_template=None,
            termo_consentimento="Leia antes do exame.",
        )
        consulta = SimpleNamespace(procedure=proc, appointment=None)
        self.assertTrue(consulta_exige_termo_listagem(consulta))

    def test_sem_termo_nao_aparece_na_lista(self):
        proc = SimpleNamespace(
            id=2,
            termo_consentimento_ativo=False,
            termo_template_id=None,
            termo_template=None,
            termo_consentimento="",
        )
        consulta = SimpleNamespace(procedure=proc, appointment=None)
        self.assertFalse(consulta_exige_termo_listagem(consulta))


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


class RenderizarTextoTermoTest(SimpleTestCase):
    def test_substitui_placeholders_da_introducao(self):
        from unittest.mock import MagicMock, patch

        from clinica_beleza.consentimento_service import renderizar_texto_termo

        consulta = MagicMock()
        consulta.loja_id = 6
        consulta.patient.nome = "LUIZ HENRIQUE FELIX"
        consulta.patient.cpf = "222.392.558-89"
        consulta.patient.email = "a@b.com"
        consulta.patient.telefone = ""
        consulta.professional.nome = "DRA. MARINA"
        consulta.professional.formatar_conselho.return_value = "CRF-SP 55604"
        consulta.professional.cpf = ""
        consulta.data_inicio = None
        proc = MagicMock()
        proc.nome = "MICROAGULHAMENTO FACIAL"
        loja = {
            "nome": "HARMONIS",
            "cnpj": "37.302.743/0001-26",
            "endereco": "PRADOPOLIS",
            "telefone": "",
            "email": "",
        }
        with patch("clinica_beleza.consentimento_service._dados_loja", return_value=loja):
            out = renderizar_texto_termo(
                "eu, {paciente_nome}, em {data} na clínica {clinica_nome}, "
                "profissional {profissional_nome}, procedimento {procedimentos}",
                consulta,
                proc,
            )
        self.assertNotIn("{paciente_nome}", out)
        self.assertNotIn("{clinica_nome}", out)
        self.assertIn("Luiz Henrique Felix", out)
        self.assertIn("Harmonis", out)
        self.assertIn("Microagulhamento Facial", out)


class LogoAssinaturaTermoTest(SimpleTestCase):
    def test_padrao_mantem_o_desenho_atual(self):
        from clinica_beleza.termos_consentimento_service import normalizar_logo_assinatura_termo

        self.assertEqual(normalizar_logo_assinatura_termo(None, None), (100, 55))
        self.assertEqual(normalizar_logo_assinatura_termo(100, 55), (100, 55))

    def test_valor_fora_da_faixa_volta_ao_padrao(self):
        from clinica_beleza.termos_consentimento_service import normalizar_logo_assinatura_termo

        self.assertEqual(normalizar_logo_assinatura_termo(10, 99), (100, 55))
