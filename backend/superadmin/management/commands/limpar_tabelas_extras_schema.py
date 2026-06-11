"""
Remove tabelas legado/não esperadas do schema de uma loja (por tipo de app).

Uso:
    python manage.py limpar_tabelas_extras_schema --slug harmonis --dry-run
    python manage.py limpar_tabelas_extras_schema --slug harmonis
    python manage.py limpar_tabelas_extras_schema --all-active --tipo clinica-beleza
"""
from django.core.management.base import BaseCommand

from superadmin.models import Loja
from superadmin.services.schema_audit_service import (
    limpar_tabelas_extras_loja,
    listar_tabelas_extras_no_schema,
)
from superadmin.services.database_schema_service import get_apps_esperados_para_loja
from core.db_config import ensure_loja_database_config
from django.db import connections


class Command(BaseCommand):
    help = 'Remove tabelas não esperadas para o tipo da loja no schema PostgreSQL.'

    def add_arguments(self, parser):
        parser.add_argument('--slug', type=str, help='Slug ou atalho da loja')
        parser.add_argument(
            '--all-active',
            action='store_true',
            help='Todas as lojas ativas com database_created',
        )
        parser.add_argument(
            '--tipo',
            type=str,
            help='Filtrar por slug do tipo (ex: clinica-beleza, crm-vendas)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas lista tabelas que seriam removidas',
        )

    def handle(self, *args, **options):
        slug = (options.get('slug') or '').strip().lower()
        all_active = options.get('all_active', False)
        tipo = (options.get('tipo') or '').strip().lower()
        dry_run = options.get('dry_run', False)

        if not slug and not all_active:
            self.stdout.write(self.style.ERROR('Informe --slug ou --all-active'))
            return

        qs = Loja.objects.select_related('tipo_loja').filter(
            is_active=True, database_created=True
        )
        if slug:
            loja = (
                qs.filter(slug__iexact=slug).first()
                or qs.filter(atalho__iexact=slug).first()
            )
            lojas = [loja] if loja else []
        else:
            lojas = list(qs.order_by('id'))
        if tipo:
            lojas = [
                l for l in lojas
                if (l.tipo_loja.slug if l.tipo_loja else '').strip().lower() == tipo
            ]

        if not lojas:
            self.stdout.write(self.style.WARNING('Nenhuma loja encontrada.'))
            return

        total_removidas = 0
        for loja in lojas:
            if dry_run:
                if not ensure_loja_database_config(loja.database_name, conn_max_age=0):
                    continue
                schema = loja.database_name.replace('-', '_')
                tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else '').strip()
                extras = listar_tabelas_extras_no_schema(
                    connections[loja.database_name],
                    schema,
                    get_apps_esperados_para_loja(loja),
                    tipo_slug=tipo_slug,
                )
                if extras:
                    self.stdout.write(f'{loja.nome}: {len(extras)} extra(s)')
                    for name in extras:
                        self.stdout.write(f'  - {name}')
                continue

            result = limpar_tabelas_extras_loja(loja)
            n = len(result.get('removidas') or [])
            total_removidas += n
            if n:
                self.stdout.write(self.style.SUCCESS(f'✅ {loja.nome}: {result["mensagem"]}'))
            else:
                self.stdout.write(f'— {loja.nome}: {result.get("mensagem", "OK")}')

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry-run: nada removido.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Concluído: {total_removidas} tabela(s) removida(s) no total.'))
