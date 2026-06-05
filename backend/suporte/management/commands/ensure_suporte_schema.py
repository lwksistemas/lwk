"""
Garante colunas/índices do app suporte no schema suporte (PostgreSQL).

Uso:
    python manage.py ensure_suporte_schema
"""
from django.core.management.base import BaseCommand
from django.db import connections


class Command(BaseCommand):
    help = 'Garante suporte_chamado.loja_slug no schema suporte.'

    def handle(self, *args, **options):
        db = 'suporte' if 'suporte' in connections.databases else 'default'
        with connections[db].cursor() as cursor:
            cursor.execute(
                """
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'suporte_chamado'
                  AND column_name = 'loja_slug'
                LIMIT 1
                """
            )
            if cursor.fetchone():
                self.stdout.write(self.style.SUCCESS('suporte_chamado.loja_slug já existe'))
                return
            cursor.execute(
                """
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = current_schema() AND table_name = 'suporte_chamado'
                LIMIT 1
                """
            )
            if not cursor.fetchone():
                self.stdout.write(self.style.WARNING('Tabela suporte_chamado não existe — rode migrate suporte'))
                return
            cursor.execute(
                'ALTER TABLE suporte_chamado ADD COLUMN IF NOT EXISTS loja_slug VARCHAR(100) DEFAULT \'\''
            )
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS suporte_chamado_loja_slug_idx ON suporte_chamado (loja_slug)'
            )
        self.stdout.write(self.style.SUCCESS('Coluna loja_slug garantida em suporte_chamado'))
