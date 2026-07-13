"""Vincula oportunidade(s) a uma empresa prestadora (Conta tipo prestadora/ambos).
Uso: python manage.py vincular_oportunidade_prestadora felix --titulo "ALFA EXCELENCIA" --prestadora ultrasis
"""
from django.core.management.base import BaseCommand
from django.db.models import Q

from core.db_config import ensure_loja_database_config
from superadmin.loja_utils import resolve_loja_by_slug_or_atalho
from tenants.middleware import set_current_loja_id, set_current_tenant_db


class Command(BaseCommand):
    help = "Vincula oportunidade(s) a uma empresa prestadora pelo título ou ID"

    def add_arguments(self, parser):
        parser.add_argument("loja", type=str, help="Slug ou atalho da loja (ex: felix)")
        parser.add_argument("--titulo", type=str, help="Trecho do título da oportunidade")
        parser.add_argument("--oportunidade-id", type=int, help="ID da oportunidade")
        parser.add_argument("--prestadora", type=str, required=True, help="Trecho do nome da prestadora")
        parser.add_argument(
            "--sync-titulo",
            action="store_true",
            help="Atualiza o título da oportunidade para o nome da prestadora (padrão das outras vendas)",
        )

    def handle(self, *args, **options):
        from crm_vendas.models import Conta, Oportunidade

        loja = resolve_loja_by_slug_or_atalho(options["loja"], is_active=True)
        if not loja:
            self.stdout.write(self.style.ERROR(f"Loja '{options['loja']}' não encontrada"))
            return

        set_current_loja_id(loja.id)
        db_name = loja.database_name or f"loja_{loja.slug}"
        if not ensure_loja_database_config(db_name):
            self.stdout.write(self.style.ERROR(f"Falha ao configurar banco {db_name}"))
            return
        set_current_tenant_db(db_name)

        prestadora_q = options["prestadora"].strip()
        ep = (
            Conta.objects.filter(loja_id=loja.id)
            .filter(Q(tipo__in=["prestadora", "ambos"]))
            .filter(Q(nome__icontains=prestadora_q) | Q(razao_social__icontains=prestadora_q))
            .first()
        )
        if not ep:
            self.stdout.write(self.style.ERROR(f"Prestadora contendo '{prestadora_q}' não encontrada"))
            self.stdout.write("Prestadoras cadastradas:")
            for c in Conta.objects.filter(loja_id=loja.id, tipo__in=["prestadora", "ambos"]):
                self.stdout.write(f"  id={c.id} nome={c.nome}")
            return

        qs = Oportunidade.objects.filter(loja_id=loja.id)
        if options.get("oportunidade_id"):
            qs = qs.filter(id=options["oportunidade_id"])
        elif options.get("titulo"):
            qs = qs.filter(titulo__icontains=options["titulo"].strip())
        else:
            self.stdout.write(self.style.ERROR("Informe --titulo ou --oportunidade-id"))
            return

        if not qs.exists():
            self.stdout.write(self.style.ERROR("Nenhuma oportunidade encontrada"))
            return

        updated = 0
        for op in qs:
            old = op.empresa_prestadora.nome if op.empresa_prestadora_id else "(nenhuma)"
            op.empresa_prestadora = ep
            update_fields = ["empresa_prestadora", "updated_at"]
            if options.get("sync_titulo") and op.titulo != ep.nome:
                op.titulo = ep.nome
                update_fields.append("titulo")
            op.save(update_fields=update_fields)
            updated += 1
            self.stdout.write(self.style.SUCCESS(
                f'✅ Oportunidade {op.id} "{op.titulo}": {old} → {ep.nome}',
            ))

        self.stdout.write(self.style.SUCCESS(f"Concluído: {updated} oportunidade(s) atualizada(s)."))
