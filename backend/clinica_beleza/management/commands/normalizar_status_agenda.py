"""
Normaliza status legado PENDING → SCHEDULED nos agendamentos das lojas.
"""
from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Converte agendamentos PENDING para SCHEDULED (remove redundância).'

    def handle(self, *args, **options):
        lojas = (
            Loja.objects.filter(is_active=True, database_created=True, tipo_loja__nome='Clínica da Beleza')
        )
        total = 0
        for loja in lojas:
            db_name = loja.database_name
            if not ensure_loja_database_config(db_name, conn_max_age=0):
                continue
            try:
                conn = connections[db_name]
                with conn.cursor() as cursor:
                    if not table_exists(cursor, 'clinica_beleza_appointment'):
                        continue
                    cursor.execute(
                        """
                        UPDATE clinica_beleza_appointment
                        SET status = 'SCHEDULED', updated_at = NOW()
                        WHERE status = 'PENDING'
                        """
                    )
                    n = cursor.rowcount or 0
                    if n:
                        total += n
                        self.stdout.write(self.style.SUCCESS(
                            f'OK loja={loja.id} ({loja.nome}): {n} PENDING → SCHEDULED'
                        ))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'ERRO loja={loja.id}: {exc}'))
            finally:
                try:
                    connections[db_name].close()
                except Exception:
                    pass

        self.stdout.write(self.style.SUCCESS(f'Concluído: {total} agendamento(s) normalizado(s).'))
