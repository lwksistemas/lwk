"""
Cancela agendamentos em aberto vinculados a pacientes inativos (soft-deleted).

Útil para limpar a agenda quando pacientes foram excluídos antes do novo
comportamento (que já cancela os agendamentos futuros na exclusão).

Uso:
    python manage.py cancel_orphan_appointments            # todas as lojas
    python manage.py cancel_orphan_appointments --slug beleza
    python manage.py cancel_orphan_appointments --dry-run   # só relata
"""
from contextlib import suppress

from django.core.management.base import BaseCommand
from django.db import connections

from core.db_config import ensure_loja_database_config
from superadmin.models import Loja

_OPEN_STATUSES = ('PENDING', 'SCHEDULED', 'CLIENT_CONFIRMED', 'PHONE_CONFIRMED', 'CONFIRMED', 'IN_PROGRESS')


def _table_exists(cursor, table: str) -> bool:
    cursor.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = current_schema() AND table_name = %s LIMIT 1
        """,
        [table],
    )
    return cursor.fetchone() is not None


class Command(BaseCommand):
    help = 'Cancela agendamentos em aberto de pacientes inativos (soft-deleted).'

    def add_arguments(self, parser):
        parser.add_argument('--slug', type=str, help='Processar apenas loja com este slug/atalho')
        parser.add_argument('--dry-run', action='store_true', help='Apenas relata, não altera nada')

    def handle(self, *args, **options):
        slug_filter = (options.get('slug') or '').strip().lower()
        dry_run = bool(options.get('dry_run'))
        lojas = Loja.objects.filter(is_active=True, database_created=True)
        total = 0
        skip = 0
        placeholders = ', '.join(['%s'] * len(_OPEN_STATUSES))

        for loja in lojas:
            if slug_filter and slug_filter not in (
                (loja.slug or '').lower(),
                (getattr(loja, 'atalho', None) or '').lower(),
            ):
                continue

            db_name = loja.database_name
            if not ensure_loja_database_config(db_name, conn_max_age=0):
                skip += 1
                self.stdout.write(self.style.WARNING(f'SKIP loja={loja.id}: banco não configurado'))
                continue

            try:
                conn = connections[db_name]
                with conn.cursor() as cursor:
                    if not _table_exists(cursor, 'clinica_beleza_appointment'):
                        skip += 1
                        continue

                    count_sql = f"""
                        SELECT COUNT(*)
                        FROM clinica_beleza_appointment a
                        JOIN clinica_beleza_patient p ON p.id = a.patient_id
                        WHERE p.is_active = FALSE
                          AND a.status IN ({placeholders})
                    """
                    cursor.execute(count_sql, list(_OPEN_STATUSES))
                    qtd = cursor.fetchone()[0]

                    if qtd and not dry_run:
                        update_sql = f"""
                            UPDATE clinica_beleza_appointment a
                            SET status = 'CANCELLED', updated_at = NOW(), version = version + 1
                            FROM clinica_beleza_patient p
                            WHERE a.patient_id = p.id
                              AND p.is_active = FALSE
                              AND a.status IN ({placeholders})
                        """
                        cursor.execute(update_sql, list(_OPEN_STATUSES))

                total += qtd
                prefix = '[dry-run] ' if dry_run else ''
                style = self.style.WARNING if dry_run else self.style.SUCCESS
                self.stdout.write(style(
                    f'{prefix}loja={loja.id} ({loja.nome}) db={db_name}: '
                    f'{qtd} agendamento(s) de pacientes inativos'
                ))
            except Exception as exc:
                skip += 1
                self.stdout.write(self.style.ERROR(f'ERRO loja={loja.id} ({loja.nome}): {exc}'))
            finally:
                with suppress(Exception):
                    connections[db_name].close()

        acao = 'encontrado(s)' if dry_run else 'cancelado(s)'
        self.stdout.write(self.style.SUCCESS(
            f'Concluído: {total} agendamento(s) {acao}, {skip} loja(s) ignorada(s).'
        ))
