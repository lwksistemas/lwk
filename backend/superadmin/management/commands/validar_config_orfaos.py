"""
Valida que a configuração de órfãos está completa: todas as tabelas com loja_id
no banco default devem estar em orfaos_config.TABELAS_LOJA_ID.

Uso: python manage.py validar_config_orfaos

Se alguma tabela com coluna loja_id (ou FK para superadmin_loja) não estiver
em TABELAS_LOJA_ID, o comando falha e lista o que falta (evita criar órfãos
ao esquecer de registrar nova tabela).
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.orfaos_config import TABELAS_LOJA_ID

# Tabelas que têm loja_id mas são de outro schema (tenant) ou não devem ser limpas no default
IGNORAR_TABELAS = {'django_migrations', 'auth_*', 'django_*', 'superadmin_loja'}  # prefixos


class Command(BaseCommand):
    help = 'Valida que todas as tabelas com loja_id no default estão em orfaos_config.TABELAS_LOJA_ID'

    def handle(self, *args, **options):
        config_tabelas = {t[0] for t in TABELAS_LOJA_ID}
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name FROM information_schema.columns
                WHERE table_schema = 'public'
                AND column_name = 'loja_id'
                AND table_name NOT LIKE 'django_%%'
                ORDER BY table_name
            """)
            tabelas_com_loja_id = [row[0] for row in cursor.fetchall()]

        faltando = [t for t in tabelas_com_loja_id if t not in config_tabelas]
        if faltando:
            self.stdout.write(self.style.ERROR(
                f'TABELAS_LOJA_ID está incompleto. Tabelas com loja_id não registradas:\n  ' +
                '\n  '.join(faltando)
            ))
            self.stdout.write(self.style.WARNING(
                '\nAdicione em superadmin/orfaos_config.py em TABELAS_LOJA_ID:\n  '
                + '\n  '.join(f"('{t}', 'loja_id')," for t in faltando)
            ))
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS(
            f'OK: Todas as {len(tabelas_com_loja_id)} tabelas com loja_id estão em TABELAS_LOJA_ID.'
        ))
