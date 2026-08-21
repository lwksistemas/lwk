"""Validade do link do termo: até finalizar a consulta, não por calendário."""
from unittest import TestCase

from clinica_beleza.consentimento_validade import termo_link_expirado_por_consulta


class TermoLinkExpiracaoTest(TestCase):
    def test_consulta_aberta_nao_expira(self):
        for status in ("RECEBER", "SCHEDULED", "IN_PROGRESS"):
            with self.subTest(status=status):
                self.assertFalse(termo_link_expirado_por_consulta(status))

    def test_consulta_finalizada_expira(self):
        for status in ("COMPLETED", "CANCELLED"):
            with self.subTest(status=status):
                self.assertTrue(termo_link_expirado_por_consulta(status))

    def test_sem_status_expira(self):
        self.assertTrue(termo_link_expirado_por_consulta(None))
        self.assertTrue(termo_link_expirado_por_consulta(""))
