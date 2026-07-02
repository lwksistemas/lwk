"""
Limpeza Evolution: órfãs (loja inexistente) + duplicatas/fantasmas (nome != ativo no DB).

Uso:
    python manage.py limpar_evolution_instancias
    python manage.py limpar_evolution_instancias --execute
    python manage.py limpar_evolution_instancias --slug felix --execute
"""
from django.core.management.base import BaseCommand

from superadmin.models import Loja
from whatsapp.evolution_cleanup import (
    cleanup_stale_and_orphan_evolution_instances,
    delete_all_evolution_instances_for_loja,
    find_instances_for_loja,
    find_orphan_evolution_instances,
    find_stale_evolution_instances,
    get_active_evolution_instance_by_loja,
    list_evolution_instances,
)
from whatsapp.evolution_client import evolution_configured


class Command(BaseCommand):
    help = 'Lista/remove instâncias Evolution órfãs e duplicadas (sessões fantasmas).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Remove instâncias órfãs/duplicadas no Evolution API',
        )
        parser.add_argument(
            '--slug',
            type=str,
            help='Loja específica (atalho ou slug): remove todas exceto a ativa no DB',
        )

    def handle(self, *args, **options):
        execute = options['execute']
        slug = (options.get('slug') or '').strip()

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('  Evolution API — limpeza órfãs e fantasmas')
        self.stdout.write('=' * 60 + '\n')

        if not evolution_configured():
            self.stdout.write(self.style.WARNING(
                'Evolution não configurado (EVOLUTION_API_URL / EVOLUTION_API_KEY).'
            ))
            return

        if slug:
            self._handle_loja(slug, execute)
            return

        todas = list_evolution_instances()
        self.stdout.write(f'Instâncias no Evolution: {len(todas)}')

        active_by_loja = get_active_evolution_instance_by_loja()
        orphans = find_orphan_evolution_instances()
        stale = find_stale_evolution_instances(active_by_loja)

        for row in active_by_loja.items():
            lid, name = row
            extras = find_instances_for_loja(lid)
            if len(extras) > 1:
                names = ', '.join(r['instance_name'] for r in extras)
                self.stdout.write(self.style.WARNING(
                    f'  Loja {lid}: {len(extras)} instância(s) [{names}] — ativa no DB: {name}'
                ))

        if orphans:
            self.stdout.write(self.style.WARNING(f'\n{len(orphans)} órfã(s) (loja inexistente):'))
            for row in orphans:
                self.stdout.write(f"  - {row['instance_name']}")

        if stale:
            self.stdout.write(self.style.WARNING(f'\n{len(stale)} duplicata(s)/fantasma(s):'))
            for row in stale:
                self.stdout.write(
                    f"  - {row['instance_name']} (ativa: {row.get('active_instance')})"
                )

        if not orphans and not stale:
            self.stdout.write(self.style.SUCCESS('\nNenhuma órfã ou duplicata.'))
            return

        if not execute:
            self.stdout.write(self.style.WARNING('\nUse --execute para remover.'))
            return

        summary = cleanup_stale_and_orphan_evolution_instances()
        self.stdout.write(self.style.SUCCESS(
            f"\nRemovidas: {summary.get('removed', 0)}, "
            f"falhas: {summary.get('failed', 0)}"
        ))

    def _handle_loja(self, slug: str, execute: bool):
        loja = Loja.objects.filter(atalho=slug).first() or Loja.objects.filter(slug=slug).first()
        if not loja:
            self.stdout.write(self.style.ERROR(f'Loja não encontrada: {slug}'))
            return

        active_by_loja = get_active_evolution_instance_by_loja()
        keep = active_by_loja.get(loja.id) or f'lwk_loja_{loja.id}'
        instances = find_instances_for_loja(loja.id)

        self.stdout.write(f'Loja {loja.nome} (id={loja.id}), ativa no DB: {keep}')
        for row in instances:
            mark = 'MANTER' if row['instance_name'] == keep else 'REMOVER'
            style = self.style.SUCCESS if mark == 'MANTER' else self.style.WARNING
            self.stdout.write(style(f"  [{mark}] {row['instance_name']}"))

        if not execute:
            self.stdout.write(self.style.WARNING('\nUse --execute para remover duplicatas.'))
            return

        results = delete_all_evolution_instances_for_loja(loja.id, keep=keep)
        ok = sum(1 for r in results if r.get('ok'))
        self.stdout.write(self.style.SUCCESS(f'\nRemovidas: {ok}/{len(results)}'))
