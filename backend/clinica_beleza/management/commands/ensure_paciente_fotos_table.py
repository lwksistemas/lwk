"""Garante a tabela clinica_beleza_paciente_fotos nos schemas das lojas.

Uso:
    python manage.py ensure_paciente_fotos_table
    python manage.py ensure_paciente_fotos_table --slug beleza
"""
from contextlib import suppress

from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import table_exists
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja

MIGRATION_NAME = "0039_paciente_foto_acompanhamento"


class Command(BaseCommand):
    help = "Cria clinica_beleza_paciente_fotos nos bancos das lojas se não existir."

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
                    if not table_exists(cursor, "clinica_beleza_consultas"):
                        skip += 1
                        continue
                    if not table_exists(cursor, "clinica_beleza_paciente_fotos"):
                        cursor.execute("""
                            CREATE TABLE clinica_beleza_paciente_fotos (
                                id BIGSERIAL PRIMARY KEY,
                                loja_id INTEGER NOT NULL,
                                patient_id BIGINT NOT NULL REFERENCES clinica_beleza_patient(id) ON DELETE CASCADE,
                                consulta_id BIGINT NOT NULL REFERENCES clinica_beleza_consultas(id) ON DELETE CASCADE,
                                cloudinary_url VARCHAR(500) NOT NULL,
                                cloudinary_public_id VARCHAR(255) NOT NULL DEFAULT '',
                                origem VARCHAR(10) NOT NULL DEFAULT 'qr',
                                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                            )
                        """)
                        cursor.execute(
                            "CREATE INDEX IF NOT EXISTS clin_cb_foto_pac_dt_idx "
                            "ON clinica_beleza_paciente_fotos (patient_id, created_at)",
                        )
                        cursor.execute(
                            "CREATE INDEX IF NOT EXISTS clin_cb_foto_cons_idx "
                            "ON clinica_beleza_paciente_fotos (consulta_id)",
                        )
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
                self.stdout.write(self.style.SUCCESS(f"   ✓ {loja.slug} ({db_name})"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ✗ {loja.slug}: {e}"))
            finally:
                with suppress(Exception):
                    connections[db_name].close()

        self.stdout.write(self.style.SUCCESS(f"\nConcluído: {ok} loja(s), {skip} ignorada(s)."))
