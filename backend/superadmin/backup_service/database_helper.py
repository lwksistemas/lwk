"""Operações de banco de dados para backup de lojas."""
import logging

from django.db import connections

from ..backup_helpers import (
    BACKUP_SAFE_IDENTIFIER_RE,
    BACKUP_SYSTEM_TABLES_EXCLUDE,
    BACKUP_TABLE_PREFIX_BLACKLIST,
    is_safe_pg_schema_token,
)

logger = logging.getLogger(__name__)

class DatabaseHelper:
    """
    Helper para operações de banco de dados.
    
    Encapsula lógica de conexão e queries ao banco isolado da loja.
    No PostgreSQL usa schema explícito (database_name com - trocado por _) para
    não depender de search_path no one-off dyno do Scheduler.
    """
    
    def __init__(self, database_name: str):
        self.database_name = database_name
        # Schema PostgreSQL = alias com hífens trocados por underscore (ex: loja_clinica_vida_5889)
        self._pg_schema = (database_name or '').replace('-', '_') if database_name else ''
    
    def get_connection(self):
        """Retorna conexão com o banco da loja"""
        return connections[self.database_name]
    
    def _is_sqlite(self) -> bool:
        """Detecta se o backend é SQLite"""
        conn = self.get_connection()
        return conn.settings_dict.get('ENGINE', '').endswith('sqlite3')
    
    def _qualified_table(self, table_name: str) -> str:
        """Retorna nome qualificado para PostgreSQL (schema.tabela) ou só tabela para SQLite."""
        if self._is_sqlite() or not self._pg_schema or not self.is_safe_table_name(table_name):
            return table_name
        if not (self._pg_schema and is_safe_pg_schema_token(self._pg_schema)):
            return table_name
        return f'"{self._pg_schema}"."{table_name}"'
    
    def qualified_table_name(self, table_name: str) -> str:
        """Nome da tabela qualificado com schema (PostgreSQL) ou só o nome (SQLite). Uso em SQL."""
        return self._qualified_table(table_name)
    
    def ensure_pg_schema_exists(self) -> bool:
        """Cria o schema no PostgreSQL se não existir (usa a conexão da loja). Retorna True se OK."""
        if self._is_sqlite() or not self._pg_schema or not is_safe_pg_schema_token(self._pg_schema):
            return True
        try:
            with self.get_connection().cursor() as cursor:
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{self._pg_schema}"')
            logger.info(f"Schema PostgreSQL '{self._pg_schema}' garantido (CREATE IF NOT EXISTS)")
            return True
        except Exception as e:
            logger.warning(f"Falha ao criar schema '{self._pg_schema}': {e}")
            return False

    def _get_current_schema_pg(self) -> str | None:
        """Retorna o schema atual da conexão (PostgreSQL). Útil quando search_path está setado."""
        if self._is_sqlite():
            return None
        try:
            with self.get_connection().cursor() as cursor:
                cursor.execute("SELECT current_schema()")
                row = cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            logger.warning(f"Erro ao obter current_schema: {e}")
            return None

    def get_all_table_names(self) -> list[str]:
        """Lista todas as tabelas do schema/banco (PostgreSQL ou SQLite). Exclui django_migrations.
        Em PostgreSQL: usa current_schema() da conexão (mesmo critério do ORM) para evitar ZIP vazio."""
        tables = []
        with self.get_connection().cursor() as cursor:
            if self._is_sqlite():
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
                )
                tables = [row[0] for row in cursor.fetchall()]
            else:
                # Usar current_schema() para listar tabelas (mesma conexão que o ORM usa no request)
                current = self._get_current_schema_pg()
                if current:
                    self._pg_schema = current
                cursor.execute(
                    """
                    SELECT tablename FROM pg_tables
                    WHERE schemaname = current_schema()
                    ORDER BY tablename
                    """
                )
                tables = [row[0] for row in cursor.fetchall()]
                if tables:
                    logger.info(f"Backup: {len(tables)} tabela(s) em current_schema()='{self._pg_schema}'")
                if not tables:
                    cursor.execute(
                        """
                        SELECT table_name FROM information_schema.tables
                        WHERE table_schema = %s AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                        """,
                        [self._pg_schema]
                    )
                    tables = [row[0] for row in cursor.fetchall()]
                # Fallback: se o schema da loja está vazio, listar do public (ORM pode estar usando public)
                if not tables and self._pg_schema and self._pg_schema != 'public':
                    cursor.execute(
                        """
                        SELECT tablename FROM pg_tables
                        WHERE schemaname = 'public'
                        ORDER BY tablename
                        """
                    )
                    tables = [row[0] for row in cursor.fetchall()]
                    if tables:
                        self._pg_schema = 'public'
                        logger.info(
                            f"Backup: 0 tabelas no schema nominal; usando schema 'public' ({len(tables)} tabela(s))"
                        )
                if not tables:
                    current = self._get_current_schema_pg()
                    logger.warning(
                        f"Backup: 0 tabelas em current_schema e em schema '{self._pg_schema}'; "
                        f"current_schema()='{current}'"
                    )
        # Excluir tabelas de sistema e prefixos proibidos (superadmin, auth, django, etc.)
        def _allow_table(name: str) -> bool:
            if name in BACKUP_SYSTEM_TABLES_EXCLUDE:
                return False
            return not any(name.startswith(prefix) for prefix in BACKUP_TABLE_PREFIX_BLACKLIST)
        return [t for t in tables if _allow_table(t)]
    
    @staticmethod
    def is_safe_table_name(name: str) -> bool:
        """Valida se o nome é seguro para uso em SQL (evita injection)."""
        return bool(name and BACKUP_SAFE_IDENTIFIER_RE.match(name))
    
    def table_exists(self, table_name: str) -> bool:
        """Verifica se uma tabela existe no banco"""
        if not self.is_safe_table_name(table_name):
            logger.warning(f"Nome de tabela inválido (segurança): {table_name!r}")
            return False
        try:
            with self.get_connection().cursor() as cursor:
                if self._is_sqlite():
                    cursor.execute(
                        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=%s",
                        [table_name]
                    )
                else:
                    if not is_safe_pg_schema_token(self._pg_schema):
                        return False
                    cursor.execute(
                        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = %s AND table_name = %s)",
                        [self._pg_schema, table_name]
                    )
                row = cursor.fetchone()
                if self._is_sqlite():
                    return row is not None
                return bool(row[0]) if row else False
        except Exception as e:
            logger.warning(f"Erro ao verificar existência da tabela {table_name}: {e}")
            return False
    
    def get_table_columns(self, table_name: str) -> list[str]:
        """Retorna lista de colunas de uma tabela"""
        if not self.is_safe_table_name(table_name):
            return []
        with self.get_connection().cursor() as cursor:
            if self._is_sqlite():
                cursor.execute(f"PRAGMA table_info({table_name})")
                return [row[1] for row in cursor.fetchall()]
            if not is_safe_pg_schema_token(self._pg_schema):
                return []
            cursor.execute(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
                """,
                [self._pg_schema, table_name]
            )
            return [row[0] for row in cursor.fetchall()]

    def _fetch_pg_attribute_meta(
        self, schema: str, table_name: str
    ) -> tuple[list[str], dict[str, tuple[bool, str]]]:
        """Uma query: nomes de colunas (ordem física) + (aceita NULL?, format_type)."""
        if not self.is_safe_table_name(table_name) or not is_safe_pg_schema_token(schema):
            return [], {}
        try:
            with self.get_connection().cursor() as cursor:
                cursor.execute(
                    """
                    SELECT a.attname,
                           a.attnotnull,
                           pg_catalog.format_type(a.atttypid, a.atttypmod)
                    FROM pg_catalog.pg_attribute a
                    INNER JOIN pg_catalog.pg_class c ON a.attrelid = c.oid
                    INNER JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
                    WHERE n.nspname = %s AND c.relname = %s
                      AND a.attnum > 0 AND NOT a.attisdropped
                    ORDER BY a.attnum
                    """,
                    [schema, table_name],
                )
                rows = cursor.fetchall()
                cols = [r[0] for r in rows]
                # attnotnull True = NOT NULL → primeiro elemento False = não aceita NULL (como is_nullable NO)
                meta = {r[0]: (not r[1], r[2] or "") for r in rows}
                return cols, meta
        except Exception as e:
            logger.warning("pg_catalog meta %s.%s: %s", schema, table_name, e)
            return [], {}

    def get_pg_table_meta_for_backup(
        self, table_name: str
    ) -> tuple[list[str], dict[str, tuple[bool, str]]]:
        """Colunas + tipos via pg_attribute; usa current_schema() e o schema nominal da loja."""
        if self._is_sqlite() or not self.is_safe_table_name(table_name):
            return [], {}
        schemas: list[str] = []
        try:
            with self.get_connection().cursor() as cur:
                cur.execute("SELECT current_schema()")
                r = cur.fetchone()
                if r and r[0] and is_safe_pg_schema_token(r[0]):
                    schemas.append(r[0])
        except Exception as e:
            logger.warning("current_schema() falhou: %s", e)
        if (
            self._pg_schema
            and is_safe_pg_schema_token(self._pg_schema)
            and self._pg_schema not in schemas
        ):
            schemas.append(self._pg_schema)
        for sch in schemas:
            if not is_safe_pg_schema_token(sch):
                continue
            cols, meta = self._fetch_pg_attribute_meta(sch, table_name)
            if cols:
                return cols, meta
        return [], {}

    def get_columns_nullable_and_type(self, table_name: str) -> dict[str, tuple[bool, str]]:
        """Retorna dict col -> (is_nullable, data_type) para colunas da tabela."""
        if not self.is_safe_table_name(table_name):
            return {}
        with self.get_connection().cursor() as cursor:
            if self._is_sqlite():
                cursor.execute(f"PRAGMA table_info({table_name})")
                return {row[1]: (row[3] == 0, row[2] or '') for row in cursor.fetchall()}
            if not is_safe_pg_schema_token(self._pg_schema):
                return {}
            cursor.execute(
                """
                SELECT column_name, is_nullable, data_type
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
                """,
                [self._pg_schema, table_name]
            )
            return {row[0]: (row[1] == 'YES', row[2] or '') for row in cursor.fetchall()}
    
    def count_records(self, table_name: str) -> int:
        """Conta registros em uma tabela"""
        if not self.is_safe_table_name(table_name):
            return 0
        qual = self._qualified_table(table_name)
        with self.get_connection().cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {qual}")
            return cursor.fetchone()[0]
    
    def _table_has_loja_id(self, table_name: str) -> bool:
        """Verifica se a tabela possui coluna loja_id (isolamento por loja)."""
        if not self.is_safe_table_name(table_name):
            return False
        columns = self.get_table_columns(table_name)
        return 'loja_id' in columns

    def fetch_all_records(
        self, table_name: str, loja_id: int | None = None
    ) -> tuple[list[str], list[tuple]]:
        """
        Busca todos os registros de uma tabela.
        Se loja_id for informado e a tabela tiver coluna loja_id, filtra apenas
        os registros daquela loja (backup com cadastros só da loja individual).

        Returns:
            Tuple com (colunas, registros)
        """
        if not self.is_safe_table_name(table_name):
            return [], []
        columns = self.get_table_columns(table_name)
        qual = self._qualified_table(table_name)
        use_loja_filter = (
            loja_id is not None
            and self._table_has_loja_id(table_name)
        )
        with self.get_connection().cursor() as cursor:
            if use_loja_filter:
                cursor.execute(
                    f'SELECT * FROM {qual} WHERE loja_id = %s',
                    [loja_id],
                )
            else:
                cursor.execute(f"SELECT * FROM {qual}")
            records = cursor.fetchall()
        return columns, records

