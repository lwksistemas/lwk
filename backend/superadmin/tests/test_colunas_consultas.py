"""Coluna Nº da listagem de Consultas precisa poder ser persistida."""
from django.test import SimpleTestCase

from superadmin.theme_colors import sanitize_colunas_consultas


class ColunasConsultasSanitizeTest(SimpleTestCase):
    def test_aceita_numero(self):
        self.assertEqual(
            sanitize_colunas_consultas(["numero", "patient", "status"]),
            ["numero", "patient", "status"],
        )

    def test_lista_sem_numero_nao_reinsere(self):
        self.assertEqual(
            sanitize_colunas_consultas(["patient", "procedure", "date", "pagamento", "status"]),
            ["patient", "procedure", "date", "pagamento", "status"],
        )
