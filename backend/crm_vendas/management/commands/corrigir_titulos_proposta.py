"""Corrige títulos de propostas existentes: remove prefixo da prestadora e mantém
só o nome (CPF) ou razão social (CNPJ) do cliente.

Uso:
  python manage.py corrigir_titulos_proposta felix --dry-run
  python manage.py corrigir_titulos_proposta felix
  python manage.py corrigir_titulos_proposta --all-lojas --dry-run
"""
from django.core.management.base import BaseCommand

from core.db_config import ensure_loja_database_config
from crm_vendas.utils import titulo_proposta_corrigido
from superadmin.loja_utils import resolve_loja_by_slug_or_atalho
from tenants.middleware import set_current_loja_id, set_current_tenant_db


class Command(BaseCommand):
    help = "Corrige títulos de propostas removendo prefixo da empresa prestadora"

    def add_arguments(self, parser):
        parser.add_argument("loja", nargs="?", type=str, help="Slug ou atalho da loja (ex: felix)")
        parser.add_argument(
            "--all-lojas",
            action="store_true",
            help="Processa todas as lojas ativas",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Mostra alterações sem gravar",
        )

    def handle(self, *args, **options):
        if options["all_lojas"]:
            from superadmin.models import Loja

            lojas = Loja.objects.filter(is_active=True).order_by("id")
            total = 0
            for loja in lojas:
                total += self._processar_loja(loja, options["dry_run"])
            self.stdout.write(self.style.SUCCESS(f"Concluído: {total} proposta(s) atualizada(s)."))
            return

        loja_arg = options.get("loja")
        if not loja_arg:
            self.stdout.write(self.style.ERROR("Informe o slug da loja ou use --all-lojas"))
            return

        loja = resolve_loja_by_slug_or_atalho(loja_arg, is_active=True)
        if not loja:
            self.stdout.write(self.style.ERROR(f"Loja '{loja_arg}' não encontrada"))
            return

        total = self._processar_loja(loja, options["dry_run"])
        self.stdout.write(self.style.SUCCESS(f"Concluído: {total} proposta(s) atualizada(s)."))

    def _processar_loja(self, loja, dry_run: bool) -> int:
        from crm_vendas.models import Proposta

        self.stdout.write(f"\n📍 Loja {loja.slug} (id={loja.id})")

        set_current_loja_id(loja.id)
        db_name = loja.database_name or f"loja_{loja.slug}"
        if not ensure_loja_database_config(db_name, conn_max_age=0):
            self.stdout.write(self.style.ERROR(f"  Falha ao configurar banco {db_name}"))
            return 0
        set_current_tenant_db(db_name)

        propostas = (
            Proposta.objects.filter(loja_id=loja.id)
            .select_related(
                "oportunidade",
                "oportunidade__lead",
                "oportunidade__lead__conta",
                "oportunidade__empresa_prestadora",
            )
            .order_by("id")
        )

        if not propostas.exists():
            self.stdout.write("  Nenhuma proposta encontrada")
            return 0

        atualizadas = 0
        for proposta in propostas:
            lead = proposta.oportunidade.lead if proposta.oportunidade_id else None
            if not lead:
                continue

            opp = proposta.oportunidade
            prestadora_nomes = []
            if opp.empresa_prestadora_id:
                ep = opp.empresa_prestadora
                prestadora_nomes.extend([
                    ep.nome,
                    ep.razao_social,
                ])
            prestadora_nomes.append(loja.nome)

            novo_titulo = titulo_proposta_corrigido(proposta.titulo, lead, prestadora_nomes)
            if not novo_titulo:
                continue

            self.stdout.write(
                f'  {"[dry-run] " if dry_run else ""}Proposta #{proposta.id} ({proposta.numero or "-"}): '
                f'"{proposta.titulo}" → "{novo_titulo}"',
            )
            if not dry_run:
                proposta.titulo = novo_titulo
                proposta.save(update_fields=["titulo", "updated_at"])
            atualizadas += 1

        return atualizadas
