from django.core.management.base import BaseCommand

from crm_vendas.vendedor_admin_service import sincronizar_vendedor_admin_owner
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Sincroniza nome/e-mail do vendedor CRM admin com o User owner da loja'

    def add_arguments(self, parser):
        parser.add_argument('--slug', type=str, help='Slug de uma loja específica')
        parser.add_argument('--dry-run', action='store_true', help='Apenas lista o que seria atualizado')

    def handle(self, *args, **options):
        slug = options.get('slug')
        dry_run = options.get('dry_run')

        qs = Loja.objects.select_related('owner', 'tipo_loja').filter(
            database_created=True,
            owner__isnull=False,
        )
        if slug:
            qs = qs.filter(slug=slug)

        total = 0
        ok = 0
        for loja in qs:
            tipo = (loja.tipo_loja.nome if loja.tipo_loja else '').strip()
            if tipo != 'CRM Vendas':
                continue
            total += 1
            owner = loja.owner
            nome_user = (owner.get_full_name() or owner.username or '').strip()
            if dry_run:
                self.stdout.write(f'[dry-run] {loja.slug}: sincronizaria admin -> {nome_user!r}')
                continue
            if sincronizar_vendedor_admin_owner(loja, owner):
                ok += 1
                self.stdout.write(self.style.SUCCESS(f'✅ {loja.slug}: {nome_user}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️ {loja.slug}: nada alterado (sem VendedorUsuario?)'))

        if dry_run:
            self.stdout.write(f'Lojas CRM elegíveis: {total}')
        else:
            self.stdout.write(self.style.SUCCESS(f'Concluído: {ok}/{total} lojas CRM atualizadas'))
