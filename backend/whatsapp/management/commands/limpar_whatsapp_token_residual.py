"""Limpa credenciais residuais da Meta Cloud API em lojas que usam Evolution.

Quando a loja migra o WhatsApp para a Evolution (whatsapp_provider='evolution'),
os campos da Cloud API da Meta (whatsapp_token e whatsapp_phone_id)
deixam de ser usados mas podem ficar com valores legados em texto no banco. Este
comando zera esses dois campos nas lojas Evolution — reduz exposição de dado sensível.
O número (whatsapp_numero) não é apagado.

Seguro por padrão (dry-run). Só grava com --commit.

Uso:
    python manage.py limpar_whatsapp_token_residual                 # simula (dry-run)
    python manage.py limpar_whatsapp_token_residual --slug clinicaharmonis
    python manage.py limpar_whatsapp_token_residual --commit        # aplica em todas
"""
from django.core.management.base import BaseCommand

from core.db_config import ensure_loja_database_config
from superadmin.models import Loja
from whatsapp.models import WhatsAppConfig


class Command(BaseCommand):
    help = "Zera token e phone_id da Meta Cloud API em lojas que usam Evolution (residual)."

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Processar apenas esta loja (slug ou atalho)")
        parser.add_argument("--commit", action="store_true", help="Aplica de fato (sem isso, só simula)")

    def handle(self, *args, **options):
        slug_filter = (options.get("slug") or "").strip().lower()
        commit = options["commit"]
        lojas = Loja.objects.filter(is_active=True, database_created=True)
        total_limpos = 0
        total_lojas = 0

        for loja in lojas:
            if slug_filter and slug_filter not in (
                (loja.slug or "").lower(),
                (getattr(loja, "atalho", None) or "").lower(),
            ):
                continue
            db_name = getattr(loja, "database_name", None)
            if not db_name or not ensure_loja_database_config(db_name, conn_max_age=0):
                continue

            try:
                # Só lojas Evolution com algum campo da Meta preenchido (residual).
                configs = WhatsAppConfig.objects.using(db_name).filter(
                    whatsapp_provider=WhatsAppConfig.PROVIDER_EVOLUTION,
                )
                for cfg in configs:
                    residuais = {
                        "whatsapp_token": (cfg.whatsapp_token or "").strip(),
                        "whatsapp_phone_id": (cfg.whatsapp_phone_id or "").strip(),
                    }
                    tem_residual = any(residuais.values())
                    if not tem_residual:
                        continue

                    total_lojas += 1
                    campos = [k for k, v in residuais.items() if v]
                    acao = "LIMPARIA" if not commit else "limpou"
                    self.stdout.write(
                        f"{loja.slug}: {acao} {', '.join(campos)} "
                        f"(provider=evolution, instância={cfg.evolution_instance_name or '-'})",
                    )

                    if commit:
                        # update() no queryset com .using(db_name) garante escrita no
                        # schema da loja (save() sem using=db grava no default/public).
                        WhatsAppConfig.objects.using(db_name).filter(pk=cfg.pk).update(
                            whatsapp_token="",
                            whatsapp_phone_id="",
                        )
                        total_limpos += 1
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"{loja.slug}: erro — {exc}"))
                continue

        self.stdout.write("")
        if total_lojas == 0:
            self.stdout.write(self.style.SUCCESS("Nenhuma credencial residual encontrada."))
        elif commit:
            self.stdout.write(self.style.SUCCESS(f"Concluído: {total_limpos} config(s) limpa(s)."))
        else:
            self.stdout.write(self.style.WARNING(
                f"DRY-RUN: {total_lojas} config(s) seriam limpas. Rode com --commit para aplicar.",
            ))
