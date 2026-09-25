"""Limpeza periódica da tabela suporte_errofrontend.

Remove duas categorias de registros desnecessários:
  1. Lojas extintas — loja_slug sem correspondência em Loja.objects ativas.
  2. Registros antigos — mais de DIAS_RETENCAO dias, de lojas ainda ativas.

Executado semanalmente via executar_cron_lwks (domingo às 3h).
Pode ser rodado manualmente: python manage.py limpar_erros_frontend
"""
import logging

from django.core.management.base import BaseCommand
from django.db import connections
from django.utils import timezone

logger = logging.getLogger(__name__)

DIAS_RETENCAO = 30  # dias que mantém erros de lojas ativas


class Command(BaseCommand):
    help = "Remove erros de frontend de lojas extintas e registros antigos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Mostra o que seria removido sem deletar.",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        prefixo = "[dry-run] " if dry_run else ""

        from superadmin.models import Loja

        slugs_ativos = set(
            Loja.objects.filter(is_active=True).values_list("slug", flat=True)
        )

        conn = connections["suporte"]
        with conn.cursor() as c:
            # 1. Erros de lojas extintas
            c.execute(
                "SELECT loja_slug, COUNT(*) FROM suporte_errofrontend"
                " GROUP BY loja_slug",
            )
            por_loja = c.fetchall()

            slugs_extintos = [s for s, _ in por_loja if s not in slugs_ativos]
            total_extintos = sum(n for s, n in por_loja if s not in slugs_ativos)

            if dry_run:
                self.stdout.write(
                    f"  [dry-run] lojas extintas: {slugs_extintos} ({total_extintos} registros)"
                )
            else:
                for slug in slugs_extintos:
                    c.execute(
                        "DELETE FROM suporte_errofrontend WHERE loja_slug = %s",
                        [slug],
                    )
                if slugs_extintos:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  Removidos {total_extintos} erros de lojas extintas: {slugs_extintos}"
                        )
                    )

            # 2. Registros antigos de lojas ativas
            corte = timezone.now() - timezone.timedelta(days=DIAS_RETENCAO)
            c.execute(
                "SELECT COUNT(*) FROM suporte_errofrontend"
                " WHERE created_at < %s",
                [corte],
            )
            total_antigos = c.fetchone()[0]

            if dry_run:
                self.stdout.write(
                    f"  [dry-run] registros > {DIAS_RETENCAO} dias: {total_antigos}"
                )
            else:
                c.execute(
                    "DELETE FROM suporte_errofrontend WHERE created_at < %s",
                    [corte],
                )
                if total_antigos:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  Removidos {total_antigos} erros com mais de {DIAS_RETENCAO} dias."
                        )
                    )

            # Contagem final
            c.execute("SELECT COUNT(*) FROM suporte_errofrontend")
            restantes = c.fetchone()[0]

        self.stdout.write(
            self.style.SUCCESS(
                f"{prefixo}limpar_erros_frontend: "
                f"{total_extintos} extintos + {total_antigos} antigos removidos. "
                f"Restam {restantes} registros."
            )
        )
        logger.info(
            "limpar_erros_frontend: extintos=%d antigos=%d restantes=%d dry_run=%s",
            total_extintos,
            total_antigos,
            restantes,
            dry_run,
        )
