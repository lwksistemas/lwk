"""Copia a logo da prestadora para prestadoras/{cnpj}. O arquivo antigo permanece.

Uso:
    python manage.py copiar_logos_prestadora
    python manage.py copiar_logos_prestadora --slug felix --aplicar
"""
import re

from django.core.management.base import BaseCommand

from core.db_config import ensure_loja_database_config
from core.media_storage import media_copiar_para_pasta, parse_media_url
from superadmin.tenant_deploy import queryset_lojas_do_app
from tenants.middleware import set_current_loja_id, set_current_tenant_db


def _digitos(valor) -> str:
    return re.sub(r"\D", "", str(valor or ""))


class Command(BaseCommand):
    help = "Copia a logo da prestadora para a pasta do CNPJ. Não apaga o arquivo antigo."

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, help="Só esta loja (slug ou atalho)")
        parser.add_argument(
            "--aplicar",
            action="store_true",
            help="Grava a nova URL. Sem esta opção, só mostra o que seria copiado.",
        )

    def handle(self, *args, **options):
        from crm_vendas.models import Conta

        slug = (options.get("slug") or "").strip().lower()
        aplicar = bool(options.get("aplicar"))
        copiadas = puladas = 0

        for loja in queryset_lojas_do_app("crm_vendas"):
            if slug and slug not in ((loja.slug or "").lower(), (getattr(loja, "atalho", None) or "").lower()):
                continue
            db_name = loja.database_name
            if not ensure_loja_database_config(db_name, conn_max_age=0):
                self.stdout.write(self.style.WARNING(f"{loja.slug}: banco indisponível"))
                continue
            set_current_loja_id(loja.id)
            set_current_tenant_db(db_name)
            contas = Conta.objects.filter(
                loja_id=loja.id,
                tipo__in=["prestadora", "ambos"],
            ).exclude(logo="")
            for conta in contas:
                cnpj = _digitos(conta.cnpj)
                if len(cnpj) != 14:
                    self.stdout.write(f"{loja.slug}: {conta.nome} sem CNPJ de 14 dígitos — logo permanece")
                    puladas += 1
                    continue
                pasta = f"prestadoras/{cnpj}"
                parsed = parse_media_url(conta.logo)
                if not parsed:
                    self.stdout.write(f"{loja.slug}: {conta.nome} logo fora do servidor de mídia — permanece")
                    puladas += 1
                    continue
                if parsed[1] == pasta:
                    continue
                if not aplicar:
                    self.stdout.write(f"{loja.slug}: copiaria {conta.nome} → {pasta}")
                    copiadas += 1
                    continue
                nova = media_copiar_para_pasta(conta.logo, pasta)
                if not nova:
                    self.stdout.write(self.style.WARNING(f"{loja.slug}: {conta.nome} cópia falhou — URL antiga permanece"))
                    puladas += 1
                    continue
                conta.logo = nova
                conta.save(update_fields=["logo"])
                self.stdout.write(self.style.SUCCESS(f"{loja.slug}: {conta.nome} copiada para {pasta}"))
                copiadas += 1

        set_current_loja_id(None)
        set_current_tenant_db("default")
        modo = "copiada(s)" if aplicar else "para copiar"
        self.stdout.write(self.style.SUCCESS(f"Concluído: {copiadas} {modo}, {puladas} permanece(m)."))
