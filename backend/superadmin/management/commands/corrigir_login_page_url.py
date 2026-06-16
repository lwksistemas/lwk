"""
Management command para corrigir login_page_url de lojas que usam slug/CPF
em vez do atalho amigável.

Uso:
  # Ver o que seria corrigido (dry-run):
  python manage.py corrigir_login_page_url

  # Aplicar correções:
  python manage.py corrigir_login_page_url --apply

  # Corrigir apenas uma loja específica:
  python manage.py corrigir_login_page_url --apply --atalho sorriso
"""
from __future__ import annotations

from django.core.management.base import BaseCommand

from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Corrige login_page_url para usar atalho amigável em vez do slug/CPF'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            default=False,
            help='Aplica as correções (sem esta flag executa em modo dry-run)',
        )
        parser.add_argument(
            '--atalho',
            type=str,
            default='',
            help='Corrigir apenas a loja com este atalho',
        )

    def handle(self, *args, **options):
        apply = options['apply']
        atalho_filtro = (options['atalho'] or '').strip().lower()

        qs = Loja.objects.exclude(atalho='').filter(is_active=True)
        if atalho_filtro:
            qs = qs.filter(atalho__iexact=atalho_filtro)

        corrigidas = 0
        ja_corretas = 0

        for loja in qs:
            url_esperada = f'/loja/{loja.atalho}/login'
            if loja.login_page_url == url_esperada:
                ja_corretas += 1
                continue

            self.stdout.write(
                f'  [{loja.id}] {loja.nome}\n'
                f'       login_page_url atual:   {loja.login_page_url!r}\n'
                f'       login_page_url correta: {url_esperada!r}\n'
            )

            if apply:
                loja.login_page_url = url_esperada
                loja.save(update_fields=['login_page_url'])
                self.stdout.write(self.style.SUCCESS('       ✅ Corrigida'))
            else:
                self.stdout.write(self.style.WARNING('       ⚠️  Dry-run — use --apply para corrigir'))

            corrigidas += 1

        self.stdout.write('')
        self.stdout.write(f'Lojas já corretas:  {ja_corretas}')
        self.stdout.write(f'Lojas {"corrigidas" if apply else "a corrigir"}: {corrigidas}')
        if not apply and corrigidas:
            self.stdout.write(self.style.WARNING('Execute com --apply para aplicar as correções.'))
