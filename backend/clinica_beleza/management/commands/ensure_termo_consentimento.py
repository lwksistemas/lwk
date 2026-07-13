"""Garante tabelas/colunas do termo de consentimento nos schemas das lojas.

Uso:
    python manage.py ensure_termo_consentimento
    python manage.py ensure_termo_consentimento --slug beleza
"""
from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import column_exists, table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja

MIGRATION_NAMES = (
    "0037_termo_consentimento_assinatura",
    "0038_termo_por_procedimento",
)


class Command(BaseCommand):
    help = "Aplica estrutura de termo de consentimento e assinatura digital nos tenants."

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Processar apenas loja com este slug/atalho")

    def handle(self, *args, **options):
        slug_filter = (options.get("slug") or "").strip().lower()
        lojas = Loja.objects.filter(is_active=True, database_created=True)
        ok = skip = 0

        for loja in lojas:
            if slug_filter and slug_filter not in (
                (loja.slug or "").lower(),
                (getattr(loja, "atalho", None) or "").lower(),
            ):
                continue
            db_name = loja.database_name
            if not ensure_loja_database_config(db_name, conn_max_age=0):
                skip += 1
                continue
            try:
                conn = connections[db_name]
                with conn.cursor() as cursor:
                    if table_exists(cursor, "clinica_beleza_procedure"):
                        if not column_exists(cursor, "clinica_beleza_procedure", "termo_consentimento"):
                            cursor.execute(
                                "ALTER TABLE clinica_beleza_procedure "
                                "ADD COLUMN termo_consentimento TEXT NOT NULL DEFAULT ''",
                            )
                        if not column_exists(cursor, "clinica_beleza_procedure", "termo_consentimento_ativo"):
                            cursor.execute(
                                "ALTER TABLE clinica_beleza_procedure "
                                "ADD COLUMN termo_consentimento_ativo BOOLEAN NOT NULL DEFAULT FALSE",
                            )
                    if table_exists(cursor, "clinica_beleza_produtoestoque") and not column_exists(cursor, "clinica_beleza_produtoestoque", "procedure_id"):
                        cursor.execute(
                            "ALTER TABLE clinica_beleza_produtoestoque "
                            "ADD COLUMN procedure_id BIGINT NULL "
                            "REFERENCES clinica_beleza_procedure(id) ON DELETE SET NULL",
                        )
                    if table_exists(cursor, "clinica_beleza_consultas"):
                        if not column_exists(cursor, "clinica_beleza_consultas", "status_assinatura_termo"):
                            cursor.execute(
                                "ALTER TABLE clinica_beleza_consultas "
                                "ADD COLUMN status_assinatura_termo VARCHAR(30) NOT NULL DEFAULT 'rascunho'",
                            )
                        if not column_exists(cursor, "clinica_beleza_consultas", "conteudo_termo_consentimento"):
                            cursor.execute(
                                "ALTER TABLE clinica_beleza_consultas "
                                "ADD COLUMN conteudo_termo_consentimento TEXT NOT NULL DEFAULT ''",
                            )
                    if not table_exists(cursor, "clinica_beleza_consulta_assinaturas_termo"):
                        cursor.execute("""
                            CREATE TABLE clinica_beleza_consulta_assinaturas_termo (
                                id BIGSERIAL PRIMARY KEY,
                                loja_id INTEGER NOT NULL,
                                consulta_id BIGINT NOT NULL REFERENCES clinica_beleza_consultas(id) ON DELETE CASCADE,
                                tipo VARCHAR(15) NOT NULL,
                                nome_assinante VARCHAR(200) NOT NULL,
                                email_assinante VARCHAR(254) NOT NULL,
                                ip_address INET NOT NULL DEFAULT '0.0.0.0',
                                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                user_agent TEXT NOT NULL DEFAULT '',
                                token VARCHAR(255) NOT NULL UNIQUE,
                                token_expira_em TIMESTAMPTZ NOT NULL,
                                assinado BOOLEAN NOT NULL DEFAULT FALSE,
                                assinado_em TIMESTAMPTZ NULL,
                                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                            )
                        """)
                        cursor.execute(
                            "CREATE INDEX clin_cb_assin_loja_tok_idx "
                            "ON clinica_beleza_consulta_assinaturas_termo (loja_id, token)",
                        )
                        cursor.execute(
                            "CREATE INDEX clin_cb_assin_cons_tipo_idx "
                            "ON clinica_beleza_consulta_assinaturas_termo (consulta_id, tipo)",
                        )
                    if not table_exists(cursor, "clinica_beleza_consulta_termo_procedimento"):
                        cursor.execute("""
                            CREATE TABLE clinica_beleza_consulta_termo_procedimento (
                                id BIGSERIAL PRIMARY KEY,
                                loja_id INTEGER NOT NULL,
                                consulta_id BIGINT NOT NULL REFERENCES clinica_beleza_consultas(id) ON DELETE CASCADE,
                                procedure_id BIGINT NOT NULL REFERENCES clinica_beleza_procedure(id) ON DELETE CASCADE,
                                conteudo_termo TEXT NOT NULL DEFAULT '',
                                status_assinatura_termo VARCHAR(30) NOT NULL DEFAULT 'rascunho',
                                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                CONSTRAINT clin_cb_termo_cons_proc_uniq UNIQUE (consulta_id, procedure_id)
                            )
                        """)
                        cursor.execute(
                            "CREATE INDEX clin_cb_termo_cons_st_idx "
                            "ON clinica_beleza_consulta_termo_procedimento (consulta_id, status_assinatura_termo)",
                        )
                    if table_exists(cursor, "clinica_beleza_consulta_assinaturas_termo") and not column_exists(
                        cursor, "clinica_beleza_consulta_assinaturas_termo", "termo_procedimento_id",
                    ):
                        cursor.execute(
                            "ALTER TABLE clinica_beleza_consulta_assinaturas_termo "
                            "ADD COLUMN termo_procedimento_id BIGINT NULL "
                            "REFERENCES clinica_beleza_consulta_termo_procedimento(id) ON DELETE CASCADE",
                        )
                        cursor.execute(
                            "CREATE INDEX clin_cb_assin_termo_tipo_idx "
                            "ON clinica_beleza_consulta_assinaturas_termo (termo_procedimento_id, tipo)",
                        )
                    for mig_name in MIGRATION_NAMES:
                        cursor.execute(
                            """
                            INSERT INTO django_migrations (app, name, applied)
                            SELECT 'clinica_beleza', %s, NOW()
                            WHERE NOT EXISTS (
                                SELECT 1 FROM django_migrations
                                WHERE app = 'clinica_beleza' AND name = %s
                            )
                            """,
                            [mig_name, mig_name],
                        )
                ok += 1
                self.stdout.write(self.style.SUCCESS(f"   ✓ {loja.slug} ({db_name})"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ✗ {loja.slug}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\nConcluído: {ok} loja(s), {skip} ignorada(s)."))
