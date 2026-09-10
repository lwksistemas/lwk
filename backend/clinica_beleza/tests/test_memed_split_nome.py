"""Regressão: prefixo de tratamento (Dra./Dr.) não pode virar primeiro nome
no cadastro enviado à Memed. Antes, 'DRA. NAYARA...' ia como nome='DRA.'.
"""
from django.test import SimpleTestCase

from clinica_beleza.memed_service import _split_nome


class SplitNomeMemedTest(SimpleTestCase):
    def test_remove_prefixo_dra_com_ponto(self):
        self.assertEqual(
            _split_nome("DRA. NAYARA DA SILVA DE SOUZA"),
            ("NAYARA", "DA SILVA DE SOUZA"),
        )

    def test_remove_prefixo_dr_minusculo(self):
        self.assertEqual(_split_nome("Dr. João Silva"), ("João", "Silva"))

    def test_sem_prefixo_inalterado(self):
        self.assertEqual(_split_nome("Maria Souza"), ("Maria", "Souza"))

    def test_nome_unico(self):
        self.assertEqual(_split_nome("Ana"), ("Ana", "Ana"))

    def test_prefixo_sem_ponto_e_nome_unico(self):
        self.assertEqual(_split_nome("Dra Paula"), ("Paula", "Paula"))

    def test_prefixos_repetidos(self):
        self.assertEqual(_split_nome("DR DRA Carlos Lima"), ("Carlos", "Lima"))

    def test_vazio(self):
        self.assertEqual(_split_nome(""), ("", ""))


class TelefoneBrMemedTest(SimpleTestCase):
    def test_remove_ddi_55(self):
        from clinica_beleza.memed_service import telefone_br_memed

        self.assertEqual(telefone_br_memed("5516997438862"), "16997438862")
        self.assertEqual(telefone_br_memed("5516992619024"), "16992619024")

    def test_formatado_vira_ddd_numero(self):
        from clinica_beleza.memed_service import telefone_br_memed

        self.assertEqual(telefone_br_memed("(16) 99743-8862"), "16997438862")

    def test_ja_sem_ddi_mantem(self):
        from clinica_beleza.memed_service import telefone_br_memed

        self.assertEqual(telefone_br_memed("16997438862"), "16997438862")
        self.assertEqual(telefone_br_memed(""), "")
