"""
Garante coluna numero_nota e tabela de produtos usados na consulta nos schemas das lojas.

Uso:
    python manage.py ensure_estoque_produto_fields
    python manage.py ensure_estoque_produto_fields --slug beleza
"""
from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import column_exists, table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Adiciona numero_nota em produtoestoque e tabela consulta_produto nos schemas das lojas.'

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
                self.stdout.write(self.style.WARNING(f'  skip {loja.slug}: DB não configurado'))
                skip += 1
                continue
            try:
                conn = connections[db_name]
                with conn.cursor() as cursor:
                    if not table_exists(cursor, 'clinica_beleza_produtoestoque'):
                        self.stdout.write(self.style.WARNING(f'  skip {loja.slug}: sem tabela estoque'))
                        skip += 1
                        continue

                    if not column_exists(cursor, 'clinica_beleza_produtoestoque', 'numero_nota'):
                        cursor.execute("""
                            ALTER TABLE clinica_beleza_produtoestoque
                            ADD COLUMN numero_nota VARCHAR(50) NOT NULL DEFAULT ''
                        """)
                        self.stdout.write(f'  {loja.slug}: coluna numero_nota adicionada')
                        cursor.execute("""
                            INSERT INTO django_migrations (app, name, applied)
                            SELECT 'clinica_beleza', '0034_consulta_produto_numero_nota', NOW()
                            WHERE NOT EXISTS (
                                SELECT 1 FROM django_migrations
                                WHERE app = 'clinica_beleza'
                                  AND name = '0034_consulta_produto_numero_nota'
                            )
                        """)

                    if (
                        table_exists(cursor, 'clinica_beleza_consulta')
                        and not table_exists(cursor, 'clinica_beleza_consultaprodutoutilizado')
                    ):
                        try:
                            cursor.execute("""
                                CREATE TABLE clinica_beleza_consultaprodutoutilizado (
                                    id BIGSERIAL PRIMARY KEY,
                                    loja_id INTEGER NOT NULL,
                                    quantidade NUMERIC(10, 2) NOT NULL,
                                    lote VARCHAR(50) NOT NULL DEFAULT '',
                                    validade DATE NULL,
                                    estoque_baixado BOOLEAN NOT NULL DEFAULT FALSE,
                                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                    consulta_id BIGINT NOT NULL
                                        REFERENCES clinica_beleza_consulta(id) ON DELETE CASCADE,
                                    produto_id BIGINT NOT NULL
                                        REFERENCES clinica_beleza_produtoestoque(id) ON DELETE RESTRICT
                                )
                            """)
                            cursor.execute(
                                'CREATE INDEX IF NOT EXISTS clinica_beleza_consultaprodutoutilizado_loja_id_idx '
                                'ON clinica_beleza_consultaprodutoutilizado (loja_id)'
                            )
                            self.stdout.write(f'  {loja.slug}: tabela consulta_produto criada')
                        except Exception as table_err:
                            self.stdout.write(self.style.WARNING(
                                f'  {loja.slug}: consulta_produto não criada ({table_err})'
                            ))

                ok += 1
                self.stdout.write(self.style.SUCCESS(f'  OK {loja.slug}'))
            except Exception as e:
                skip += 1
                self.stdout.write(self.style.ERROR(f'  ERRO {loja.slug}: {e}'))
            finally:
                try:
                    connections[db_name].close()
                except Exception:
                    pass

        self.stdout.write(self.style.SUCCESS(f'Concluído: {ok} loja(s), {skip} ignorada(s)/erro.'))
