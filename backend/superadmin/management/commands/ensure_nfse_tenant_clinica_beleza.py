"""Aplica migrations crm_vendas + nfse_integration em lojas Clínica da Beleza (NFS-e)."""

from django.core.management.base import BaseCommand

from crm_vendas.schema_service import configurar_schema_crm_loja
from superadmin.models import Loja

TIPOS_CLINICA = (
    "clinica-beleza",
    "clinica-da-beleza",
    "clinica-estetica",
    "clinica-de-estetica",
)


class Command(BaseCommand):
    help = "Provisiona tabelas CRMConfig + NFSe nos schemas de lojas clinica-beleza"

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Processar apenas esta loja")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        qs = Loja.objects.filter(
            is_active=True,
            database_created=True,
            tipo_loja__slug__in=TIPOS_CLINICA,
        ).select_related("tipo_loja")
        if options.get("slug"):
            qs = qs.filter(slug=options["slug"])

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.WARNING("Nenhuma loja clinica-beleza encontrada."))
            return

        ok_count = 0
        for loja in qs:
            if options.get("dry_run"):
                self.stdout.write(f"[dry-run] {loja.slug} ({loja.tipo_loja.slug})")
                ok_count += 1
                continue
            self.stdout.write(f"Configurando NFS-e tenant: {loja.slug}…")
            if configurar_schema_crm_loja(loja):
                ok_count += 1
                self.stdout.write(self.style.SUCCESS(f"  OK {loja.slug}"))
            else:
                self.stderr.write(self.style.ERROR(f"  Falha {loja.slug}"))

        self.stdout.write(self.style.SUCCESS(f"Concluído: {ok_count}/{total} loja(s)."))
