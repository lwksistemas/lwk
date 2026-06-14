"""
Garante schema PostgreSQL suporte, tabelas do app e coluna loja_slug.

Uso:
    python manage.py ensure_suporte_schema
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connections


def _is_postgres_suporte() -> bool:
    if 'suporte' not in connections.databases:
        return False
    engine = connections.databases['suporte'].get('ENGINE', '')
    return 'postgresql' in engine


def _schema_exists(cursor) -> bool:
    cursor.execute(
        "SELECT 1 FROM information_schema.schemata WHERE schema_name = 'suporte' LIMIT 1"
    )
    return cursor.fetchone() is not None


def _table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'suporte' AND table_name = %s
        LIMIT 1
        """,
        [table_name],
    )
    return cursor.fetchone() is not None


def _column_exists(cursor, table_name: str, column_name: str) -> bool:
    cursor.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'suporte'
          AND table_name = %s
          AND column_name = %s
        LIMIT 1
        """,
        [table_name, column_name],
    )
    return cursor.fetchone() is not None


class Command(BaseCommand):
    help = 'Garante schema suporte, migrations e suporte_chamado.loja_slug (PostgreSQL).'

    def handle(self, *args, **options):
        if not _is_postgres_suporte():
            self.stdout.write(self.style.WARNING('Banco suporte PostgreSQL não configurado — ignorando'))
            return

        with connections['default'].cursor() as cursor:
            cursor.execute('CREATE SCHEMA IF NOT EXISTS suporte')
            self.stdout.write(self.style.SUCCESS('Schema PostgreSQL suporte garantido'))

            if not _table_exists(cursor, 'suporte_chamado'):
                self.stdout.write(
                    self.style.WARNING('Tabela suporte_chamado ausente — recriando schema suporte…')
                )
                cursor.execute('DROP SCHEMA IF EXISTS suporte CASCADE')
                cursor.execute('CREATE SCHEMA suporte')
                for app in ('contenttypes', 'auth', 'sessions', 'suporte'):
                    call_command('migrate', app, database='suporte', interactive=False, verbosity=1)

            if not _table_exists(cursor, 'suporte_chamado'):
                self.stdout.write(
                    self.style.ERROR(
                        'suporte_chamado ainda não existe após migrate — verifique logs do banco suporte'
                    )
                )
                return

            self.stdout.write(self.style.SUCCESS('Tabela suporte_chamado presente no schema suporte'))

            if _column_exists(cursor, 'suporte_chamado', 'loja_slug'):
                self.stdout.write(self.style.SUCCESS('suporte_chamado.loja_slug já existe'))
                return

        with connections['suporte'].cursor() as cursor:
            cursor.execute(
                "ALTER TABLE suporte_chamado ADD COLUMN IF NOT EXISTS loja_slug VARCHAR(100) DEFAULT ''"
            )
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS suporte_chamado_loja_slug_idx ON suporte_chamado (loja_slug)'
            )
        self.stdout.write(self.style.SUCCESS('Coluna loja_slug garantida em suporte_chamado'))
