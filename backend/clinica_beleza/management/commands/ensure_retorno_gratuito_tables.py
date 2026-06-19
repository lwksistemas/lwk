"""Garante tabelas/colunas de retorno gratuito (migration 0047) nos schemas das lojas."""
from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import ensure_retorno_gratuito_tables, table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Cria config/regras de retorno gratuito e colunas em appointment/consulta (IF NOT EXISTS).'

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
                continue

            try:
                conn = connections[db_name]
                with conn.cursor() as cursor:
                    if not table_exists(cursor, 'clinica_beleza_appointment'):
                        skip += 1
                        continue
                    before_config = table_exists(cursor, 'clinica_beleza_agenda_retorno_config')
                    ensure_retorno_gratuito_tables(cursor)
                    after_config = table_exists(cursor, 'clinica_beleza_agenda_retorno_config')

                if not before_config and after_config:
                    ok += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'OK loja={loja.id} ({loja.nome}) db={db_name}: retorno gratuito criado'
                    ))
                else:
                    skip += 1
                    self.stdout.write(f'OK (já existe) loja={loja.id} ({loja.nome})')
            except Exception as exc:
                skip += 1
                self.stdout.write(self.style.ERROR(f'ERRO loja={loja.id} ({loja.nome}): {exc}'))
            finally:
                try:
                    connections[db_name].close()
                except Exception:
                    pass

        self.stdout.write(self.style.SUCCESS(f'Concluído: {ok} loja(s) atualizada(s), {skip} ignorada(s).'))
