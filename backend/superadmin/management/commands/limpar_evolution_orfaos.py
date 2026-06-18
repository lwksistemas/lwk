"""
Remove instâncias Evolution (lwk_loja_{id}) sem loja correspondente no LWK.

Uso:
    python manage.py limpar_evolution_orfaos              # listar
    python manage.py limpar_evolution_orfaos --execute    # remover
"""
from django.core.management.base import BaseCommand

from superadmin.models import Loja
from whatsapp.evolution_cleanup import (
    delete_orphan_evolution_instances,
    find_orphan_evolution_instances,
    list_evolution_instances,
)
from whatsapp.evolution_client import evolution_configured


class Command(BaseCommand):
    help = 'Lista/remove instâncias Evolution órfãs (lwk_loja_{id} sem loja no sistema).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Remove instâncias órfãs no Evolution API',
        )

    def handle(self, *args, **options):
        execute = options['execute']

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('  Evolution API — instâncias lwk_loja_*')
        self.stdout.write('=' * 60 + '\n')

        if not evolution_configured():
            self.stdout.write(self.style.WARNING(
                'Evolution não configurado (EVOLUTION_API_URL / EVOLUTION_API_KEY).'
            ))
            return

        loja_ids = set(Loja.objects.values_list('id', flat=True))
        todas = list_evolution_instances()
        self.stdout.write(f'Instâncias no Evolution: {len(todas)}')
        for row in todas:
            lid = row.get('loja_id')
            name = row['instance_name']
            if lid is None:
                self.stdout.write(f'  - {name} (nome fora do padrão lwk_loja_{{id}})')
            elif lid in loja_ids:
                loja = Loja.objects.filter(id=lid).values_list('nome', 'slug').first()
                loja_txt = f'{loja[0]} ({loja[1]})' if loja else '?'
                self.stdout.write(self.style.SUCCESS(f'  OK {name} → loja {lid}: {loja_txt}'))
            else:
                self.stdout.write(self.style.WARNING(f'  ÓRFÃ {name} → loja_id {lid} NÃO existe no LWK'))

        orphans = find_orphan_evolution_instances(loja_ids)
        if not orphans:
            self.stdout.write(self.style.SUCCESS('\nNenhuma instância órfã.'))
            return

        self.stdout.write(self.style.WARNING(f'\n{len(orphans)} instância(s) órfã(s):'))
        for row in orphans:
            self.stdout.write(f"  - {row['instance_name']} (loja_id={row['loja_id']})")

        if not execute:
            self.stdout.write(self.style.WARNING(
                '\nUse --execute para remover no Evolution API.'
            ))
            return

        results = delete_orphan_evolution_instances(loja_ids)
        ok = sum(1 for r in results if r.get('ok'))
        fail = len(results) - ok
        self.stdout.write(self.style.SUCCESS(f'\nRemovidas: {ok}, falhas: {fail}'))
