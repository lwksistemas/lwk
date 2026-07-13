"""Remove instâncias Evolution (lwk_loja_{id}) sem loja correspondente no LWK.

Uso:
    python manage.py limpar_evolution_orfaos              # listar
    python manage.py limpar_evolution_orfaos --execute    # remover (seguro)

Duplicatas/fantasmas (loja ativa com várias instâncias): use
    python manage.py limpar_evolution_instancias --execute
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from superadmin.models import Loja
from whatsapp.evolution_cleanup import (
    classify_evolution_instances,
    delete_orphan_evolution_instances,
    list_evolution_instances,
)
from whatsapp.evolution_client import evolution_configured


class Command(BaseCommand):
    help = "Lista/remove instâncias Evolution órfãs (lwk_loja_{id} sem loja no sistema)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Remove instâncias órfãs no Evolution API (seguro se Evolution dedicada)",
        )
        parser.add_argument(
            "--force-cross-environment",
            action="store_true",
            help="Remove instâncias de lojas de outro ambiente (Evolution compartilhada)",
        )

    def handle(self, *args, **options):
        execute = options["execute"]
        force_cross = options["force_cross_environment"]

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("  Evolution API — instâncias lwk_loja_*")
        env = getattr(settings, "LWK_ENVIRONMENT", "production")
        self.stdout.write(f"  Ambiente: {env}")
        self.stdout.write("=" * 60 + "\n")

        if not evolution_configured():
            self.stdout.write(self.style.WARNING(
                "Evolution não configurado (EVOLUTION_API_URL / EVOLUTION_API_KEY).",
            ))
            return

        loja_ids = set(Loja.objects.values_list("id", flat=True))
        todas = list_evolution_instances()
        classified = classify_evolution_instances(loja_ids)
        shared = classified["shared_evolution"]

        self.stdout.write(f"Instâncias no Evolution: {len(todas)}")
        for row in todas:
            lid = row.get("loja_id")
            name = row["instance_name"]
            if lid is None:
                self.stdout.write(f"  - {name} (nome fora do padrão lwk_loja_{{id}})")
            elif lid in loja_ids:
                loja = Loja.objects.filter(id=lid).values_list("nome", "slug").first()
                loja_txt = f"{loja[0]} ({loja[1]})" if loja else "?"
                self.stdout.write(self.style.SUCCESS(f"  OK {name} → loja {lid}: {loja_txt}"))
            elif shared:
                self.stdout.write(self.style.WARNING(
                    f"  CROSS-ENV {name} → loja_id {lid} (outro ambiente LWK)",
                ))
            else:
                self.stdout.write(self.style.WARNING(f"  ÓRFÃ {name} → loja_id {lid} NÃO existe no LWK"))

        cross = classified["cross_environment"]
        if not cross:
            self.stdout.write(self.style.SUCCESS("\nNenhuma instância órfã/cross-env."))
            return

        label = "cross-environment" if shared else "órfã(s)"
        self.stdout.write(self.style.WARNING(f"\n{len(cross)} instância(s) {label}:"))
        for row in cross:
            self.stdout.write(f"  - {row['instance_name']} (loja_id={row['loja_id']})")

        if shared and not force_cross:
            self.stdout.write(self.style.ERROR(
                "\nEvolution compartilhada: NÃO execute sem --force-cross-environment.",
            ))
            return

        if not execute:
            self.stdout.write(self.style.WARNING(
                "\nUse --execute para remover no Evolution API.",
            ))
            return

        results = delete_orphan_evolution_instances(
            loja_ids,
            allow_cross_environment=force_cross,
        )
        ok = sum(1 for r in results if r.get("ok"))
        fail = len(results) - ok
        self.stdout.write(self.style.SUCCESS(f"\nRemovidas: {ok}, falhas: {fail}"))
