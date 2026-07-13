"""Orquestra correção de schema das lojas Clínica da Beleza.

Delega para corrigir_schema_clinica_beleza (já aplica migrations + ensure_*).
Útil como ponto único de entrada em docs/scripts.

Uso:
    python manage.py ensure_all_clinica_beleza
    python manage.py ensure_all_clinica_beleza --slug beta
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Orquestra ensure/migrations de todas as lojas Clínica da Beleza"

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Slug/CNPJ de uma loja")
        parser.add_argument("--loja-id", type=int, help="ID de uma loja")

    def handle(self, *args, **options):
        kwargs = {}
        if options.get("slug"):
            kwargs["slug"] = options["slug"]
        if options.get("loja_id"):
            kwargs["loja_id"] = options["loja_id"]
        self.stdout.write(">> ensure_all_clinica_beleza → corrigir_schema_clinica_beleza")
        call_command("corrigir_schema_clinica_beleza", **kwargs)
