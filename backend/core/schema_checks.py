"""Checagem de tabela e coluna no schema atual. Não pertence a um app."""
def is_sqlite(cursor) -> bool:
    return getattr(cursor.db, "vendor", None) == "sqlite" or "sqlite" in str(cursor.connection).lower()


def table_exists(cursor, table: str) -> bool:
    if is_sqlite(cursor):
        cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=%s LIMIT 1",
            [table],
        )
    else:
        cursor.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = current_schema() AND table_name = %s LIMIT 1
            """,
            [table],
        )
    return cursor.fetchone() is not None


def column_exists(cursor, table: str, column: str) -> bool:
    if is_sqlite(cursor):
        cursor.execute(f"PRAGMA table_info({table})")
        return any(row[1] == column for row in cursor.fetchall())
    cursor.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = %s AND column_name = %s
        LIMIT 1
        """,
        [table, column],
    )
    return cursor.fetchone() is not None
