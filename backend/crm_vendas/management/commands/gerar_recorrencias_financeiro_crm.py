"""Gera lançamentos a partir de recorrências financeiras CRM vencidas."""
from django.core.management.base import BaseCommand

from core.db_config import ensure_loja_database_config
from crm_vendas.services_recorrencia_financeiro import processar_recorrencias_pendentes
from superadmin.models import Loja
from tenants.middleware import set_current_loja_id, set_current_tenant_db


class Command(BaseCommand):
    help = "Gera lançamentos de despesas/receitas recorrentes do CRM (por loja tenant)."

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Processar apenas esta loja (slug ou atalho)")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        slug_filter = (options.get("slug") or "").strip().lower()
        dry_run = bool(options.get("dry_run"))
        total_criadas = 0

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
                continue

            set_current_loja_id(loja.id)
            set_current_tenant_db(db_name)
            out = processar_recorrencias_pendentes(loja.id, dry_run=dry_run)
            total_criadas += out["criadas"]
            self.stdout.write(
                f'{loja.slug}: criadas={out["criadas"]} ignoradas={out["ignoradas"]} '
                f'encerradas={out["encerradas"]}',
            )

        set_current_loja_id(None)
        set_current_tenant_db("default")
        self.stdout.write(self.style.SUCCESS(f"Concluído. Lançamentos gerados: {total_criadas}"))
