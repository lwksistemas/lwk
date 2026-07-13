"""Garante tabelas do módulo financeiro CRM (migration 0064) nos schemas das lojas.

Uso:
    python manage.py ensure_crm_financeiro_tabelas
    python manage.py ensure_crm_financeiro_tabelas --slug felix
"""
from django.core.management.base import BaseCommand
from django.db import connections

from clinica_beleza.schema_ensure import table_exists
from core.db_config import ensure_loja_database_config
from crm_vendas.financeiro_schema_ensure import (
    TABLE_GRUPO,
    TABLE_LANCAMENTO,
    TABLE_RECORRENCIA,
    aplicar_financeiro_base_sql,
    aplicar_recorrencia_sql,
    ensure_financeiro_tabelas,
)
from crm_vendas.schema_service import configurar_schema_crm_loja
from superadmin.models import Loja


class Command(BaseCommand):
    help = "Aplica migrations financeiro CRM (0064+) em lojas que ainda não têm as tabelas."

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Processar apenas loja com este slug/atalho")

    def handle(self, *args, **options):
        slug_filter = (options.get("slug") or "").strip().lower()
        ok = skip = fixed = 0

        lojas = Loja.objects.filter(is_active=True, database_created=True).select_related("tipo_loja")
        for loja in lojas:
            tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else "").strip()
            if tipo_slug != "crm-vendas":
                continue
            if slug_filter and slug_filter not in (
                (loja.slug or "").lower(),
                (getattr(loja, "atalho", None) or "").lower(),
            ):
                continue

            db_name = loja.database_name
            if not ensure_loja_database_config(db_name, conn_max_age=0):
                self.stdout.write(self.style.WARNING(f"Pulando {loja.slug}: DB indisponível"))
                skip += 1
                continue

            schema_name = db_name.replace("-", "_")
            try:
                conn = connections[db_name]
                with conn.cursor() as cursor:
                    cursor.execute(f'SET search_path TO "{schema_name}", public')
                    tem_grupo = table_exists(cursor, TABLE_GRUPO)
                    tem_lanc = table_exists(cursor, TABLE_LANCAMENTO)
                    tem_rec = table_exists(cursor, TABLE_RECORRENCIA)

                if tem_grupo and tem_lanc and tem_rec:
                    self.stdout.write(f"{loja.slug}: tabelas financeiro OK")
                    ok += 1
                    continue

                with conn.cursor() as cursor:
                    if not tem_grupo or not tem_lanc:
                        self.stdout.write(
                            self.style.WARNING(
                                f"{loja.slug}: criando tabelas base (grupo={tem_grupo}, "
                                f"lancamento={tem_lanc}) via SQL",
                            ),
                        )
                        if not aplicar_financeiro_base_sql(cursor, schema_name):
                            skip += 1
                            self.stdout.write(self.style.ERROR(f"{loja.slug}: falha SQL base"))
                            continue
                        tem_grupo = tem_lanc = True
                        fixed += 1

                    if tem_grupo and tem_lanc and not tem_rec and aplicar_recorrencia_sql(cursor, schema_name):
                        fixed += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"{loja.slug}: tabelas financeiro criadas (SQL)"),
                        )
                        continue

                if not (tem_grupo and tem_lanc and tem_rec):
                    self.stdout.write(
                        self.style.WARNING(f"{loja.slug}: fallback migrate via configurar_schema_crm_loja"),
                    )
                    if configurar_schema_crm_loja(loja):
                        with conn.cursor() as cursor:
                            if ensure_financeiro_tabelas(cursor, schema_name):
                                fixed += 1
                                self.stdout.write(
                                    self.style.SUCCESS(f"{loja.slug}: schema financeiro corrigido"),
                                )
                            else:
                                skip += 1
                                self.stdout.write(self.style.ERROR(f"{loja.slug}: tabelas ainda ausentes"))
                    else:
                        skip += 1
                        self.stdout.write(self.style.ERROR(f"{loja.slug}: falha ao corrigir schema"))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"{loja.slug}: {exc}"))
                skip += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Concluído: {ok} OK, {fixed} corrigida(s), {skip} pulada(s)/falha(s).",
            ),
        )
