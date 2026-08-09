"""Management command para auditar URLs antigas do Cloudinary em schemas tenants.

Verifica tabelas de fotos/pacientes da clínica e gera relatório CSV/JSON.

Uso:
    python manage.py audit_cloudinary_urls --output /tmp/audit_cloudinary.json
    python manage.py audit_cloudinary_urls --csv /tmp/audit_cloudinary.csv
    python manage.py audit_cloudinary_urls --limit 50
"""
import csv
import json
from urllib.parse import urlparse

from django.core.management.base import BaseCommand
from django.db import connection


CLOUDINARY_HOSTS = (
    "res.cloudinary.com",
    "cloudinary.com",
)

TARGETS = [
    {
        "table": "clinica_beleza_paciente_fotos",
        "url_columns": ["url"],
        "extra_columns": ["id", "consulta_id", "patient_id", "origem"],
    },
    {
        "table": "clinica_beleza_patient",
        "url_columns": ["foto_url"],
        "extra_columns": ["id", "nome", "loja_id"],
    },
]


class Command(BaseCommand):
    help = "Audita URLs antigas do Cloudinary em schemas tenants."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            default=None,
            help="Caminho para salvar o relatório em JSON.",
        )
        parser.add_argument(
            "--csv",
            type=str,
            default=None,
            help="Caminho para salvar o relatório em CSV.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limitar número de schemas a verificar.",
        )

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            self.stdout.write(
                self.style.WARNING(
                    "⚠️ Este comando é destinado a ambientes PostgreSQL com schemas tenants."
                )
            )
            return

        schemas = self._get_tenant_schemas()
        if options["limit"]:
            schemas = schemas[: options["limit"]]

        findings = []
        for schema in schemas:
            for target in TARGETS:
                rows = self._find_cloudinary_urls(
                    schema, target["table"], target["url_columns"], target["extra_columns"]
                )
                for row in rows:
                    for col in target["url_columns"]:
                        url = row.get(col)
                        if url and self._is_cloudinary(url):
                            findings.append(
                                {
                                    "schema": schema,
                                    "table": target["table"],
                                    "url_column": col,
                                    "url": url,
                                    **{k: row.get(k) for k in target["extra_columns"]},
                                }
                            )

        total = len(findings)
        schemas_with_issues = sorted({f["schema"] for f in findings})

        self.stdout.write(
            self.style.SUCCESS(f"🔍 Auditado {len(schemas)} schemas.")
        )
        if total == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "✅ Nenhuma URL do Cloudinary encontrada."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️ {total} registro(s) com URL do Cloudinary em "
                    f"{len(schemas_with_issues)} schema(s)."
                )
            )
            for schema in schemas_with_issues[:10]:
                count = sum(1 for f in findings if f["schema"] == schema)
                self.stdout.write(f"   - {schema}: {count}")
            if len(schemas_with_issues) > 10:
                self.stdout.write(f"   ... e mais {len(schemas_with_issues) - 10}")

        if options["output"]:
            with open(options["output"], "w", encoding="utf-8") as fp:
                json.dump(findings, fp, ensure_ascii=False, indent=2)
            self.stdout.write(f"💾 JSON salvo em {options['output']}")

        if options["csv"]:
            with open(options["csv"], "w", newline="", encoding="utf-8") as fp:
                if findings:
                    writer = csv.DictWriter(fp, fieldnames=findings[0].keys())
                    writer.writeheader()
                    writer.writerows(findings)
                else:
                    fp.write("schema,table,url_column,url\n")
            self.stdout.write(f"💾 CSV salvo em {options['csv']}")

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

    def _find_cloudinary_urls(self, schema, table, url_columns, extra_columns):
        columns = ", ".join(
            connection.ops.quote_name(c) for c in extra_columns + url_columns
        )
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    f"""
                    SELECT {columns}
                    FROM {connection.ops.quote_name(schema)}.{connection.ops.quote_name(table)}
                    WHERE {' OR '.join(f"{connection.ops.quote_name(c)} LIKE '%%cloudinary%%'" for c in url_columns)}
                    LIMIT 10000
                    """
                )
                rows = [
                    dict(zip(extra_columns + url_columns, row))
                    for row in cursor.fetchall()
                ]
                return rows
            except Exception as exc:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠️ {schema}.{table}: {exc}")
                )
                return []

    def _is_cloudinary(self, url: str) -> bool:
        try:
            host = urlparse(url).hostname or ""
        except Exception:
            return False
        return any(h in host for h in CLOUDINARY_HOSTS)
