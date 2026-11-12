"""Identificação da clínica e do profissional na primeira página do termo."""
from types import SimpleNamespace
from unittest import TestCase

from clinica_beleza.termo_identificacao import (
    endereco_completo_loja,
    linhas_clinica_termo,
    linhas_profissional_termo,
)


class EnderecoClinicaTermoTest(TestCase):
    def test_endereco_completo_com_cep_e_telefone(self):
        loja = SimpleNamespace(
            nome="HARMONIS - CLINICA DE ESTETICA AVANCADA & SAUDE LTDA",
            nome_fantasia="HARMONIS",
            cpf_cnpj="37302743000126",
            logradouro="Rua das Flores",
            numero="120",
            complemento="Sala 2",
            bairro="Centro",
            cidade="Pradópolis",
            uf="SP",
            cep="14850000",
            telefone_contato="16999998888",
            email_contato="",
        )
        linhas = dict(linhas_clinica_termo(loja))
        self.assertEqual(linhas["Nome fantasia"], "Harmonis")
        self.assertEqual(
            linhas["Razão social"],
            "Harmonis - Clinica de Estetica Avancada & Saude Ltda",
        )
        self.assertEqual(linhas["CNPJ"], "37.302.743/0001-26")
        self.assertEqual(
            linhas["Endereço"],
            "Rua das Flores, 120, Sala 2, Centro, Pradópolis - SP, CEP 14850-000",
        )
        self.assertEqual(linhas["Telefone"], "(16) 99999-8888")

    def test_so_cidade_nao_usa_campo_endereco_inexistente(self):
        loja = SimpleNamespace(nome="HARMONIS", cpf_cnpj="", cidade="PRADOPOLIS", uf="")
        self.assertEqual(endereco_completo_loja(loja), "PRADOPOLIS")
        self.assertNotIn("Nome fantasia", dict(linhas_clinica_termo(loja)))
        self.assertEqual(dict(linhas_clinica_termo(loja))["Razão social"], "Harmonis")

    def test_telefone_com_codigo_do_pais_e_texto_em_caixa_alta(self):
        loja = SimpleNamespace(
            nome="HARMONIS - CLINICA DE ESTETICA AVANCADA & SAUDE LTDA",
            cpf_cnpj="37.302.743/0001-26",
            logradouro="SAO MARTINHO",
            numero="833",
            complemento="",
            bairro="CENTRO",
            cidade="PRADOPOLIS",
            uf="SP",
            cep="14850000",
            telefone_contato="5516997842341",
        )
        linhas = dict(linhas_clinica_termo(loja))
        self.assertEqual(linhas["Telefone"], "(16) 99784-2341")
        self.assertEqual(
            linhas["Razão social"],
            "Harmonis - Clinica de Estetica Avancada & Saude Ltda",
        )
        self.assertEqual(
            linhas["Endereço"],
            "Sao Martinho, 833, Centro, Pradopolis - SP, CEP 14850-000",
        )

    def test_telefone_cai_no_contato_do_administrador(self):
        loja = SimpleNamespace(
            nome="Clinica",
            telefone_contato="",
            owner_telefone="1633334444",
        )
        self.assertEqual(dict(linhas_clinica_termo(loja))["Telefone"], "(16) 3333-4444")


class ProfissionalTermoTest(TestCase):
    def test_nome_conselho_e_registro_do_profissional_do_procedimento(self):
        prof = SimpleNamespace(
            nome="NAYARA DA SILVA DE SOUZA",
            conselho="COREN",
            conselho_uf="SP",
            registro_profissional="356480",
        )
        self.assertEqual(
            linhas_profissional_termo(prof),
            [
                ("Profissional", "Nayara da Silva de Souza"),
                ("Conselho", "COREN-SP"),
                ("Registro", "356480"),
            ],
        )

    def test_sem_campos_usa_formatar_conselho(self):
        prof = SimpleNamespace(nome="DRA. MARINA", formatar_conselho=lambda: "CRF-SP 55604")
        self.assertEqual(
            linhas_profissional_termo(prof),
            [("Profissional", "Dra. Marina"), ("Conselho", "CRF-SP 55604")],
        )


class CaixaAltaTermoTest(TestCase):
    def test_texto_juridico_fica_com_a_primeira_letra_maiuscula(self):
        from clinica_beleza.termo_identificacao import normalizar_caixa_termo

        texto = (
            "Através do presente TERMO DE CONSENTIMENTO LIVRE E ESCLARECIDO, eu, Cris Bossoni "
            "Stoianovi, formalizo no consultório Harmonis - Clinica de Estetica Avancada & Saude Ltda "
            "o procedimento com TOXINA BOTULÍNICA a que me submeterei.\n"
            "I. DO PROCEDIMENTO e DA INDICAÇÃO\n"
            "RISCOS PRECOCES\n"
            "Declaro que NÃO estou grávida e que NÃO HÁ POSSIBILIDADE de estar.\n"
            "XI. DO RESULTADO FINAL E DA OBRIGAÇÃO ASSUMIDA PELO(A) PROFISSIONAL\n"
            "XII. DA LEI GERAL DE PROTEÇÃO DE DADOS - LGPD\n"
            "Eu estou ciente de que NÃO HÁ GARANTIA DE RESULTADO FINAL"
        )
        out = normalizar_caixa_termo(texto)
        self.assertIn("termo de consentimento livre e esclarecido", out)
        self.assertIn("toxina botulínica", out)
        self.assertIn("Cris Bossoni Stoianovi", out)
        self.assertIn("Harmonis - Clinica de Estetica Avancada & Saude Ltda", out)
        self.assertIn("I. Do procedimento e da indicação", out)
        self.assertIn("Riscos precoces", out)
        self.assertIn("não estou grávida e que não há possibilidade", out)
        self.assertIn("XI. Do resultado final e da obrigação assumida pelo(a) profissional", out)
        self.assertIn("XII. Da lei geral de proteção de dados - LGPD", out)
        self.assertIn("não há garantia de resultado final", out)
        self.assertNotIn("TERMO DE CONSENTIMENTO", out)
        self.assertNotIn("TOXINA BOTULÍNICA", out)
