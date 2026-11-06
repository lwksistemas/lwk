"""O deploy não pode regravar número de consulta que já existe."""
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase

from clinica_beleza.management.commands.ensure_consulta_numero import SQL_NUMERAR_SEM_NUMERO


def _compacto(sql: str) -> str:
    return " ".join(sql.split()).lower()


class _Cursor:
    def __init__(self):
        self.executed = []
        self.rowcount = 0

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class _Conn:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor

    def close(self):
        return None


class EnsureConsultaNumeroTest(SimpleTestCase):
    def test_sql_so_preenche_numero_vazio_a_partir_do_maximo(self):
        sql = _compacto(SQL_NUMERAR_SEM_NUMERO)
        self.assertIn("where numero is null", sql)
        self.assertIn("coalesce(max(numero), 0)", sql)
        self.assertIn("base.max_numero + faltantes.rn", sql)
        trecho_da_sequencia = sql.split("row_number()", 1)[1]
        self.assertIn("where numero is null", trecho_da_sequencia)

    @patch("clinica_beleza.management.commands.ensure_consulta_numero.column_exists", return_value=True)
    @patch("clinica_beleza.management.commands.ensure_consulta_numero.table_exists", return_value=True)
    @patch("clinica_beleza.management.commands.ensure_consulta_numero.ensure_loja_database_config", return_value=True)
    @patch("clinica_beleza.management.commands.ensure_consulta_numero.lojas_clinica_beleza_com_schema")
    @patch("clinica_beleza.management.commands.ensure_consulta_numero.connections")
    def test_o_comando_nao_regrava_numero_existente(self, connections, lojas, _db, _tabela, _coluna):
        cursor = _Cursor()
        connections.__getitem__.return_value = _Conn(cursor)
        lojas.return_value = [
            SimpleNamespace(
                id=6,
                nome="Clinica",
                slug="loja-teste",
                atalho="",
                cnpj="",
                database_name="loja_teste",
            ),
        ]

        saida = StringIO()
        call_command("ensure_consulta_numero", stdout=saida)

        updates = [sql for sql, _params in cursor.executed if "UPDATE clinica_beleza_consultas" in sql]
        self.assertEqual(updates, [SQL_NUMERAR_SEM_NUMERO])
        self.assertEqual(cursor.executed[0][1], [6])
        self.assertIn("0 consulta(s) sem número preenchida(s)", saida.getvalue())
