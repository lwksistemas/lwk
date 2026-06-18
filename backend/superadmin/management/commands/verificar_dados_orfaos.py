"""
Verifica registros no schema public com loja_id inexistente (tabelas de orfaos_config).

Uso:
    python manage.py verificar_dados_orfaos
    python manage.py verificar_dados_orfaos --remover
"""
from django.core.management.base import BaseCommand
from django.db import connection

from superadmin.models import Loja
from superadmin.orfaos_config import TABELAS_LOJA_ID_DEFAULT


class Command(BaseCommand):
    help = 'Verifica/remove registros com loja_id sem loja correspondente (schema public).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--remover',
            action='store_true',
            help='Remove registros órfãos encontrados',
        )

    def handle(self, *args, **options):
        remover = options['remover']
        lojas_ids = set(Loja.objects.values_list('id', flat=True))
        total = 0

        self.stdout.write('Registros com loja_id inválido (schema public):\n')
        for tabela, coluna in TABELAS_LOJA_ID_DEFAULT:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""
                        SELECT COUNT(*) FROM {tabela}
                        WHERE {coluna} IS NOT NULL
                          AND {coluna} NOT IN (SELECT id FROM superadmin_loja)
                        """
                    )
                    count = cursor.fetchone()[0]
                    if count > 0:
                        total += count
                        self.stdout.write(self.style.WARNING(f'  {tabela}: {count}'))
                        if remover:
                            cursor.execute(
                                f"""
                                DELETE FROM {tabela}
                                WHERE {coluna} NOT IN (SELECT id FROM superadmin_loja)
                                """
                            )
                            self.stdout.write(self.style.SUCCESS(f'    → removidos {count}'))
            except Exception as exc:
                if 'does not exist' not in str(exc).lower():
                    self.stdout.write(self.style.ERROR(f'  {tabela}: {exc}'))

        if total == 0:
            self.stdout.write(self.style.SUCCESS('Nenhum registro órfão por loja_id.'))
        elif not remover:
            self.stdout.write(self.style.WARNING('\nUse --remover para limpar.'))
