"""Management command para verificar se as migrações 0066/0067 de clinica_beleza
foram aplicadas em todos os schemas tenants.

Uso:
    python manage.py check_clinica_migrations
    python manage.py check_clinica_migrations --fix
    python manage.py check_clinica_migrations --limit 10
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = (
        "Verifica se as migrações 0066 (rename colunas paciente_fotos) e 0067 "
        "(campos NFS-e) foram aplicadas em todos os schemas de clinica_beleza."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Tenta aplicar as alterações faltantes via SQL idempotente (somente PostgreSQL).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limitar número de schemas a verificar.",
        )

    def handle(self, *args, **options):
        fix = options["fix"]
        limit = options["limit"]

        if connection.vendor != "postgresql":
            self.stdout.write(
                self.style.WARNING(
                    "⚠️ Este comando é destinado a ambientes PostgreSQL com schemas tenants."
                )
            )
            return

        schemas = self._get_tenant_schemas()
        if limit:
            schemas = schemas[:limit]

        self.stdout.write(
            self.style.SUCCESS(f"🔍 Verificando {len(schemas)} schemas...")
        )

        missing_migrations = set()
        missing_cols_0066 = set()
        missing_cols_0067 = set()

        for schema in schemas:
            ok_migration = self._check_migrations(schema)
            ok_0066 = self._check_0066(schema)
            ok_0067 = self._check_0067(schema)

            status = []
            if not ok_migration["0066"]:
                missing_migrations.add(schema)
                status.append("0066 não registrada")
            if not ok_migration["0067"]:
                missing_migrations.add(schema)
                status.append("0067 não registrada")
            if not ok_0066:
                missing_cols_0066.add(schema)
                status.append("colunas 0066 faltando")
            if not ok_0067:
                missing_cols_0067.add(schema)
                status.append("colunas 0067 faltando")

            if status:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠️ {schema}: {', '.join(status)}")
                )
                if fix:
                    self._apply_fix(schema)
            else:
                self.stdout.write(f"  ✅ {schema}: OK")

        total_missing = len(
            missing_migrations | missing_cols_0066 | missing_cols_0067
        )

        if total_missing == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "\n✅ Todos os schemas estão com 0066/0067 aplicadas."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠️ {total_missing} schema(s) com pendências."
                )
            )
            if fix:
                self.stdout.write(
                    self.style.SUCCESS(
                        "Modo --fix ativado; alterações foram aplicadas. "
                        "Reexecute sem --fix para confirmar."
                    )
                )

    def _get_tenant_schemas(self):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name NOT IN ('public', 'information_schema', 'pg_catalog', 'pg_toast')
                ORDER BY schema_name
                """
            )
            return [row[0] for row in cursor.fetchall()]

    def _check_migrations(self, schema):
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT name
                FROM {connection.ops.quote_name(schema)}.django_migrations
                WHERE app = 'clinica_beleza' AND name IN ('0066_paciente_foto_rename_db_columns', '0067_nfse_config_padrao_nacional_fields')
                """
            )
            rows = {row[0] for row in cursor.fetchall()}
        return {
            "0066": "0066_paciente_foto_rename_db_columns" in rows,
            "0067": "0067_nfse_config_padrao_nacional_fields" in rows,
        }

    def _check_0066(self, schema):
        """Verifica se as colunas de paciente_fotos estão renomeadas corretamente."""
        if not self._table_exists(schema, "clinica_beleza_paciente_fotos"):
            return True
        expected = {"url", "public_id"}
        forbidden = {"cloudinary_url", "cloudinary_public_id"}
        return self._check_columns(
            schema, "clinica_beleza_paciente_fotos", expected, forbidden
        )

    def _check_0067(self, schema):
        """Verifica se os campos novos da ClinicaBelezaNfseConfig existem."""
        if not self._table_exists(schema, "clinica_beleza_clinicabelezanfseconfig"):
            # Loja sem módulo NFS-e / tabela ainda não criada — não é falha de 0067.
            return True
        expected = {
            "issnet_usar_padrao_nacional",
            "codigo_tributacao_nacional",
            "codigo_tributacao_municipal",
            "nacional_codigo_municipio",
            "indicador_operacao",
            "cst_ibscbs",
            "cclass_trib_ibscbs",
            "p_tot_trib_sn",
        }
        return self._check_columns(
            schema, "clinica_beleza_clinicabelezanfseconfig", expected, set()
        )

    def _table_exists(self, schema, table_name) -> bool:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = %s AND table_name = %s
                LIMIT 1
                """,
                [schema, table_name],
            )
            return cursor.fetchone() is not None

    def _check_columns(self, schema, table_name, expected, forbidden):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                """,
                [schema, table_name],
            )
            columns = {row[0] for row in cursor.fetchall()}

        if not columns:
            return False
        if forbidden and forbidden.intersection(columns):
            return False
        return expected.issubset(columns)

    def _apply_fix(self, schema):
        """Aplica SQL idempotente para resolver pendências em um schema."""
        qn = connection.ops.quote_name
        with connection.cursor() as cursor:
            # 0066: renomeia colunas se existirem com nomes antigos
            if self._table_exists(schema, "clinica_beleza_paciente_fotos"):
                for old_name, new_name in [
                    ("cloudinary_url", "url"),
                    ("cloudinary_public_id", "public_id"),
                ]:
                    cursor.execute(
                        f"""
                        DO $$
                        BEGIN
                            IF EXISTS (
                                SELECT 1 FROM information_schema.columns
                                WHERE table_schema = %s AND table_name = 'clinica_beleza_paciente_fotos'
                                AND column_name = %s
                            ) AND NOT EXISTS (
                                SELECT 1 FROM information_schema.columns
                                WHERE table_schema = %s AND table_name = 'clinica_beleza_paciente_fotos'
                                AND column_name = %s
                            ) THEN
                                ALTER TABLE {qn(schema)}.clinica_beleza_paciente_fotos
                                RENAME COLUMN {qn(old_name)} TO {qn(new_name)};
                            END IF;
                        END $$;
                        """,
                        [schema, old_name, schema, new_name],
                    )

            # 0067: só altera se a tabela de config NFS-e já existir neste schema
            if self._table_exists(schema, "clinica_beleza_clinicabelezanfseconfig"):
                for col_name, col_def in [
                    (
                        "issnet_usar_padrao_nacional",
                        "boolean NOT NULL DEFAULT TRUE",
                    ),
                    ("codigo_tributacao_nacional", "varchar(10) NOT NULL DEFAULT ''"),
                    ("codigo_tributacao_municipal", "varchar(10) NOT NULL DEFAULT ''"),
                    ("nacional_codigo_municipio", "varchar(7) NOT NULL DEFAULT ''"),
                    ("indicador_operacao", "varchar(2) NOT NULL DEFAULT ''"),
                    ("cst_ibscbs", "varchar(3) NOT NULL DEFAULT ''"),
                    ("cclass_trib_ibscbs", "varchar(6) NOT NULL DEFAULT ''"),
                    ("p_tot_trib_sn", "numeric(5,2)"),
                ]:
                    cursor.execute(
                        f"""
                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1 FROM information_schema.columns
                                WHERE table_schema = %s
                                  AND table_name = 'clinica_beleza_clinicabelezanfseconfig'
                                  AND column_name = %s
                            ) THEN
                                ALTER TABLE {qn(schema)}.clinica_beleza_clinicabelezanfseconfig
                                ADD COLUMN {qn(col_name)} {col_def};
                            END IF;
                        END $$;
                        """,
                        [schema, col_name],
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"    ⏭️ {schema}: tabela NFS-e ausente — use "
                        "corrigir_schema_clinica_beleza / migrate no tenant."
                    )
                )

            # Registra as migrações como aplicadas apenas quando as tabelas-alvo existem
            if self._table_exists(schema, "clinica_beleza_paciente_fotos"):
                cursor.execute(
                    f"""
                    INSERT INTO {qn(schema)}.django_migrations (app, name, applied)
                    SELECT 'clinica_beleza', %s, NOW()
                    WHERE NOT EXISTS (
                        SELECT 1 FROM {qn(schema)}.django_migrations
                        WHERE app = 'clinica_beleza' AND name = %s
                    );
                    """,
                    [
                        "0066_paciente_foto_rename_db_columns",
                        "0066_paciente_foto_rename_db_columns",
                    ],
                )
            if self._table_exists(schema, "clinica_beleza_clinicabelezanfseconfig"):
                cursor.execute(
                    f"""
                    INSERT INTO {qn(schema)}.django_migrations (app, name, applied)
                    SELECT 'clinica_beleza', %s, NOW()
                    WHERE NOT EXISTS (
                        SELECT 1 FROM {qn(schema)}.django_migrations
                        WHERE app = 'clinica_beleza' AND name = %s
                    );
                    """,
                    [
                        "0067_nfse_config_padrao_nacional_fields",
                        "0067_nfse_config_padrao_nacional_fields",
                    ],
                )

        self.stdout.write(self.style.SUCCESS(f"    🔧 Correções aplicadas em {schema}"))
