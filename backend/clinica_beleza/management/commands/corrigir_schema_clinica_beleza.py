"""Aplica migrations e comandos ensure_* nas lojas Clínica da Beleza.

Uso:
    python manage.py corrigir_schema_clinica_beleza
    python manage.py corrigir_schema_clinica_beleza --slug 31682991890
    python manage.py corrigir_schema_clinica_beleza --loja-id 16
"""
from django.core.management.base import BaseCommand
from django.db.models import Q

from clinica_beleza.catalogo_service import lojas_clinica_beleza_com_schema
from superadmin.services.schema_audit_service import corrigir_loja


class Command(BaseCommand):
    help = "Corrige schema de lojas Clínica da Beleza (migrations + ensure_*)"

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Slug/CNPJ de uma loja")
        parser.add_argument("--loja-id", type=int, help="ID de uma loja")

    def handle(self, *args, **options):
        qs = lojas_clinica_beleza_com_schema(apenas_ativas=True)
        if options.get("slug"):
            ident = options["slug"].strip()
            qs = qs.filter(Q(slug=ident) | Q(atalho__iexact=ident))
        if options.get("loja_id"):
            qs = qs.filter(id=options["loja_id"])

        lojas = list(qs.order_by("id"))
        if not lojas:
            self.stdout.write(self.style.WARNING("Nenhuma loja Clínica da Beleza encontrada."))
            return

        self.stdout.write(f"Processando {len(lojas)} loja(s)...\n")
        ok = 0
        for loja in lojas:
            self.stdout.write(f"📦 {loja.nome} (id={loja.id}, slug={loja.slug})")
            result = corrigir_loja(loja)
            if result.get("sucesso"):
                ok += 1
                self.stdout.write(self.style.SUCCESS(f'   ✅ {result.get("mensagem", "OK")}'))
            else:
                self.stdout.write(self.style.WARNING(f'   ⚠️ {result.get("mensagem", "Falha")}'))

            from django.db import connection

            from clinica_beleza.schema_ensure import table_exists
            from core.db_config import ensure_loja_database_config

            if ensure_loja_database_config(loja.database_name):
                schema = loja.database_name.replace("-", "_")
                with connection.cursor() as cursor:
                    cursor.execute(f'SET search_path TO "{schema}", public')
                    tem_agenda = table_exists(cursor, "clinica_beleza_appointment")
                self.stdout.write(
                    self.style.SUCCESS("   📅 clinica_beleza_appointment: sim")
                    if tem_agenda
                    else self.style.ERROR("   📅 clinica_beleza_appointment: NÃO"),
                )
            self.stdout.write("")

        self.stdout.write(self.style.SUCCESS(f"Concluído: {ok}/{len(lojas)} lojas corrigidas."))
