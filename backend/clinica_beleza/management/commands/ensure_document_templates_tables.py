"""Garante tabelas clinica_beleza_document_templates e clinica_beleza_documentos_clinicos
nos bancos/schemas das lojas.

Cria as tabelas (via schema_editor, exatamente como o modelo define) quando não
existem e marca a migration 0029_document_templates_and_documentos como aplicada,
evitando conflito quando migrate_all_lojas rodar depois.

Uso:
    python manage.py ensure_document_templates_tables
    python manage.py ensure_document_templates_tables --slug beleza
"""
from contextlib import suppress

from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.models import DocumentoClinico, DocumentTemplate
from clinica_beleza.schema_ensure import table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja

MIGRATION_NAME = "0029_document_templates_and_documentos"
TABLE_TEMPLATE = "clinica_beleza_document_templates"
TABLE_DOCUMENTO = "clinica_beleza_documentos_clinicos"




class Command(BaseCommand):
    help = "Cria clinica_beleza_document_templates e clinica_beleza_documentos_clinicos nos bancos das lojas."

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Processar apenas loja com este slug/atalho")

    def handle(self, *args, **options):
        slug_filter = (options.get("slug") or "").strip().lower()
        lojas = Loja.objects.filter(is_active=True, database_created=True)
        ok = 0
        skip = 0

        for loja in lojas:
            if slug_filter and slug_filter not in (
                (loja.slug or "").lower(),
                (getattr(loja, "atalho", None) or "").lower(),
            ):
                continue

            db_name = loja.database_name
            if not ensure_loja_database_config(db_name, conn_max_age=0):
                skip += 1
                self.stdout.write(self.style.WARNING(f"SKIP loja={loja.id}: banco não configurado"))
                continue

            try:
                conn = connections[db_name]
                with conn.cursor() as cursor:
                    # A tabela base (clinica_beleza_professional) precisa existir.
                    if not table_exists(cursor, "clinica_beleza_professional"):
                        skip += 1
                        self.stdout.write(self.style.WARNING(
                            f"SKIP loja={loja.id} ({loja.nome}): tabela clinica_beleza_professional não existe",
                        ))
                        continue

                    template_existia = table_exists(cursor, TABLE_TEMPLATE)
                    documento_existia = table_exists(cursor, TABLE_DOCUMENTO)

                # Criar tabelas que não existem (ordem importa: template antes de documento por FK)
                criadas = []
                if not template_existia:
                    with conn.schema_editor() as schema_editor:
                        schema_editor.create_model(DocumentTemplate)
                    criadas.append(TABLE_TEMPLATE)

                if not documento_existia:
                    with conn.schema_editor() as schema_editor:
                        schema_editor.create_model(DocumentoClinico)
                    criadas.append(TABLE_DOCUMENTO)

                with conn.cursor() as cursor:
                    # Marca a migration como aplicada para não conflitar com migrate_all_lojas.
                    cursor.execute(
                        """
                        INSERT INTO django_migrations (app, name, applied)
                        SELECT 'clinica_beleza', %s, NOW()
                        WHERE NOT EXISTS (
                            SELECT 1 FROM django_migrations
                            WHERE app = 'clinica_beleza' AND name = %s
                        )
                        """,
                        [MIGRATION_NAME, MIGRATION_NAME],
                    )

                ok += 1
                if criadas:
                    detalhe = f'tabelas criadas: {", ".join(criadas)}'
                else:
                    detalhe = "ambas já existiam"
                self.stdout.write(self.style.SUCCESS(
                    f"OK loja={loja.id} ({loja.nome}) db={db_name}: {detalhe}",
                ))
            except Exception as exc:
                skip += 1
                self.stdout.write(self.style.ERROR(f"ERRO loja={loja.id} ({loja.nome}): {exc}"))
            finally:
                with suppress(Exception):
                    connections[db_name].close()

        self.stdout.write(self.style.SUCCESS(
            f"\nConcluído: {ok} loja(s) atualizada(s), {skip} ignorada(s).",
        ))
