"""
Management command para corrigir oportunidades closed_won sem data_fechamento_ganho
e closed_lost sem data_fechamento_perdido.

Usa data_fechamento como fallback, ou created_at se nenhuma data estiver disponível.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Corrige oportunidades fechadas sem data_fechamento_ganho/perdido preenchida'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loja-id',
            type=int,
            help='ID da loja específica para corrigir (se não informado, corrige todas)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra o que seria corrigido, sem alterar dados',
        )

    def handle(self, *args, **options):
        loja_id = options.get('loja_id')
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('=== DRY RUN — nenhuma alteração será feita ==='))

        lojas = Loja.objects.using('default').filter(
            tipo_loja__slug='crm-vendas',
            is_active=True,
            database_created=True,
        )
        if loja_id:
            lojas = lojas.filter(id=loja_id)

        total_corrigidas_ganho = 0
        total_corrigidas_perdido = 0

        for loja in lojas:
            db_name = loja.database_name
            if not db_name:
                continue
            schema_name = db_name.replace('-', '_')

            try:
                with connection.cursor() as cursor:
                    # Verificar se a tabela existe neste schema
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_schema = %s
                            AND table_name = 'crm_vendas_oportunidade'
                        );
                    """, [schema_name])
                    if not cursor.fetchone()[0]:
                        continue

                    cursor.execute(f'SET search_path TO "{schema_name}", public;')

                    # Contar closed_won sem data_fechamento_ganho
                    cursor.execute("""
                        SELECT COUNT(*) FROM crm_vendas_oportunidade
                        WHERE etapa = 'closed_won' AND data_fechamento_ganho IS NULL;
                    """)
                    count_ganho = cursor.fetchone()[0]

                    # Contar closed_lost sem data_fechamento_perdido
                    cursor.execute("""
                        SELECT COUNT(*) FROM crm_vendas_oportunidade
                        WHERE etapa = 'closed_lost' AND data_fechamento_perdido IS NULL;
                    """)
                    count_perdido = cursor.fetchone()[0]

                    if count_ganho > 0:
                        self.stdout.write(
                            f'  Loja {loja.id} ({loja.nome}): {count_ganho} closed_won sem data_fechamento_ganho'
                        )
                        if not dry_run:
                            # Usar data_fechamento como fallback, senão created_at::date
                            cursor.execute("""
                                UPDATE crm_vendas_oportunidade
                                SET data_fechamento_ganho = COALESCE(data_fechamento, created_at::date)
                                WHERE etapa = 'closed_won' AND data_fechamento_ganho IS NULL;
                            """)
                            total_corrigidas_ganho += count_ganho

                    if count_perdido > 0:
                        self.stdout.write(
                            f'  Loja {loja.id} ({loja.nome}): {count_perdido} closed_lost sem data_fechamento_perdido'
                        )
                        if not dry_run:
                            cursor.execute("""
                                UPDATE crm_vendas_oportunidade
                                SET data_fechamento_perdido = COALESCE(data_fechamento, created_at::date)
                                WHERE etapa = 'closed_lost' AND data_fechamento_perdido IS NULL;
                            """)
                            total_corrigidas_perdido += count_perdido

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Erro na loja {loja.id} ({loja.nome}): {e}'))
                continue

        self.stdout.write('')
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'DRY RUN: {total_corrigidas_ganho + total_corrigidas_perdido} oportunidade(s) seriam corrigidas '
                f'({total_corrigidas_ganho} closed_won + {total_corrigidas_perdido} closed_lost)'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'✅ Corrigidas: {total_corrigidas_ganho} closed_won + {total_corrigidas_perdido} closed_lost'
            ))
