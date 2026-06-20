"""
Garante a coluna foto_url em clinica_beleza_patient (schemas das lojas).

Uso:
    python manage.py ensure_patient_foto_url
    python manage.py ensure_patient_foto_url --slug vida
"""
from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import column_exists, ensure_patient_foto_url_column, table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Adiciona foto_url em clinica_beleza_patient nos bancos das lojas.'

    def add_arguments(self, parser):
        parser.add_argument('--slug', type=str, help='Processar apenas loja com este slug/atalho')

    def handle(self, *args, **options):
        slug_filter = (options.get('slug') or '').strip().lower()
        lojas = Loja.objects.filter(is_active=True, database_created=True)
        ok = skip = 0

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
                    if not table_exists(cursor, 'clinica_beleza_patient'):
                        skip += 1
                        continue
                    had_column = column_exists(cursor, 'clinica_beleza_patient', 'foto_url')
                    ensure_patient_foto_url_column(cursor)

                ok += 1
                detalhe = 'já existia' if had_column else 'coluna adicionada'
                self.stdout.write(self.style.SUCCESS(
                    f'OK loja={loja.id} ({loja.nome}) db={db_name}: foto_url — {detalhe}'
                ))
            except Exception as exc:
                skip += 1
                self.stdout.write(self.style.ERROR(f'ERRO loja={loja.id} ({loja.nome}): {exc}'))
            finally:
                try:
                    connections[db_name].close()
                except Exception:
                    pass

        self.stdout.write(self.style.SUCCESS(f'Concluído: {ok} loja(s) atualizada(s), {skip} ignorada(s).'))
