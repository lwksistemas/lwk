"""
Converte Payments PAID/PARTIAL de consultas ainda não finalizadas em DRAFT.

Assim o Financeiro (caixa/comissões) só conta após Finalizar.
Idempotente — seguro no releaseCommand via ensure_all.
"""
from contextlib import suppress

from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Payment PAID/PARTIAL de consulta não finalizada → DRAFT (fora do Financeiro).'

    def handle(self, *args, **options):
        lojas = Loja.objects.filter(
            is_active=True,
            database_created=True,
            tipo_loja__nome='Clínica da Beleza',
        )
        total = 0
        for loja in lojas:
            db_name = loja.database_name
            if not ensure_loja_database_config(db_name, conn_max_age=0):
                continue
            try:
                conn = connections[db_name]
                with conn.cursor() as cursor:
                    if not table_exists(cursor, 'clinica_beleza_payment'):
                        continue
                    if not table_exists(cursor, 'clinica_beleza_consultas'):
                        continue
                    cursor.execute(
                        """
                        UPDATE clinica_beleza_payment p
                        SET status = 'DRAFT',
                            payment_date = NULL,
                            updated_at = NOW()
                        FROM clinica_beleza_consultas c
                        WHERE c.appointment_id = p.appointment_id
                          AND c.status <> 'COMPLETED'
                          AND c.status <> 'CANCELLED'
                          AND p.status IN ('PAID', 'PARTIAL')
                        """
                    )
                    n = cursor.rowcount or 0
                    if n:
                        total += n
                        self.stdout.write(self.style.SUCCESS(
                            f'OK loja={loja.id} ({loja.nome}): {n} payment(s) → DRAFT'
                        ))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'ERRO loja={loja.id}: {exc}'))
            finally:
                with suppress(Exception):
                    connections[db_name].close()

        self.stdout.write(self.style.SUCCESS(
            f'Concluído: {total} payment(s) convertidos para DRAFT.'
        ))
