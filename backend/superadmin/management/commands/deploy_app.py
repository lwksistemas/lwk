"""Atalho: migrate + ensure só de um (ou mais) apps, só nas lojas que usam esse app."""
from django.core.management import call_command
from django.core.management.base import BaseCommand

from superadmin.tenant_deploy import parse_apps_option


class Command(BaseCommand):
    help = (
        "Deploy pontual de app(s) nos tenants. "
        "Ex.: python manage.py deploy_app clinica_beleza"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "apps",
            nargs="+",
            help="App(s) Django, ex.: clinica_beleza  ou  crm_vendas whatsapp",
        )
        parser.add_argument(
            "--tipo",
            action="append",
            dest="tipos",
            help="Restringir a tipo_loja.slug. Ex.: clinica-beleza",
        )

    def handle(self, *args, **options):
        apps = parse_apps_option(options.get("apps"))
        if not apps:
            self.stderr.write("Informe ao menos um app.")
            return
        tipos = parse_apps_option(options.get("tipos"))
        self.stdout.write(f"Deploy pontual: {', '.join(apps)}")
        migrate_kw = {"apps": apps}
        if tipos:
            migrate_kw["tipos"] = tipos
        call_command("migrate_all_lojas", **migrate_kw)
        call_command("ensure_all", apps=apps)
