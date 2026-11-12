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
        self.assertEqual(linhas["Nome fantasia"], "HARMONIS")
        self.assertEqual(
            linhas["Razão social"],
            "HARMONIS - CLINICA DE ESTETICA AVANCADA & SAUDE LTDA",
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
        self.assertEqual(dict(linhas_clinica_termo(loja))["Razão social"], "HARMONIS")

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
                ("Profissional", "NAYARA DA SILVA DE SOUZA"),
                ("Conselho", "COREN-SP"),
                ("Registro", "356480"),
            ],
        )

    def test_sem_campos_usa_formatar_conselho(self):
        prof = SimpleNamespace(nome="DRA. MARINA", formatar_conselho=lambda: "CRF-SP 55604")
        self.assertEqual(
            linhas_profissional_termo(prof),
            [("Profissional", "DRA. MARINA"), ("Conselho", "CRF-SP 55604")],
        )
