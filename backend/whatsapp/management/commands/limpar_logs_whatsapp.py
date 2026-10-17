"""Apaga logs de WhatsApp mais antigos que N dias, em cada loja.

O histórico de acessos já sai no cron de domingo. Este comando faz o mesmo
com whatsapp_whatsapplog, que vive no schema da loja.

Uso:
    python manage.py limpar_logs_whatsapp --dry-run
    python manage.py limpar_logs_whatsapp --dias=90
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.db_config import ensure_loja_database_config
from superadmin.models import Loja
from whatsapp.models import WhatsAppLog


class Command(BaseCommand):
    help = "Remove logs de WhatsApp mais antigos que N dias (padrão: 90)."

    def add_arguments(self, parser):
        parser.add_argument("--dias", type=int, default=90, help="Dias a manter (padrão: 90)")
        parser.add_argument("--dry-run", action="store_true", help="Só conta, não apaga")
        parser.add_argument("--slug", type=str, help="Apenas esta loja (slug ou atalho)")

    def handle(self, *args, **options):
        dias = max(1, int(options["dias"]))
        dry_run = options["dry_run"]
        slug = (options.get("slug") or "").strip().lower()
        limite = timezone.now() - timedelta(days=dias)
        self.stdout.write(f"Logs de WhatsApp anteriores a {timezone.localtime(limite):%d/%m/%Y}")

        lojas = Loja.objects.filter(is_active=True, database_created=True)
        total = 0
        for loja in lojas:
            if slug and slug not in (
                (loja.slug or "").lower(),
                (getattr(loja, "atalho", None) or "").lower(),
            ):
                continue
            db = getattr(loja, "database_name", None)
            if not db or not ensure_loja_database_config(db, conn_max_age=0):
                continue
            try:
                qs = WhatsAppLog.objects.using(db).filter(created_at__lt=limite)
                n = qs.count()
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"{loja.slug}: indisponível ({exc})"))
                continue
            if n == 0:
                continue
            total += n
            if dry_run:
                self.stdout.write(f"{loja.slug}: {n} logs seriam apagados")
                continue
            apagados = qs.delete()[0]
            self.stdout.write(f"{loja.slug}: {apagados} logs apagados")

        if total == 0:
            self.stdout.write(self.style.SUCCESS("Nenhum log antigo."))
            return
        if dry_run:
            self.stdout.write(self.style.WARNING(f"Dry-run: {total} logs no total."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Apagados {total} logs."))
