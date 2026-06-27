"""Desativa tipo legado CLIEST e migra lojas remanescentes para CLIBEL (Clínica da Beleza)."""

from django.core.management.base import BaseCommand

from superadmin.models import Loja, TipoLoja


class Command(BaseCommand):
    help = 'Desativa tipo CLIEST (clinica-estetica legado) e migra lojas para CLIBEL'

    def handle(self, *args, **options):
        cliest = TipoLoja.objects.filter(codigo='CLIEST').first()
        clibel = TipoLoja.objects.filter(codigo='CLIBEL').first()

        if not clibel:
            self.stderr.write(self.style.ERROR('Tipo CLIBEL não encontrado. Rode criar_tipos_app_iniciais.'))
            return

        if not cliest:
            self.stdout.write(self.style.WARNING('Tipo CLIEST não encontrado — nada a migrar.'))
            return

        lojas = Loja.objects.filter(tipo_loja=cliest)
        count = lojas.count()
        if count:
            slugs = list(lojas.values_list('slug', flat=True))
            lojas.update(tipo_loja=clibel)
            self.stdout.write(
                self.style.SUCCESS(f'Migradas {count} loja(s) CLIEST → CLIBEL: {", ".join(slugs)}')
            )
        else:
            self.stdout.write('Nenhuma loja com tipo CLIEST.')

        if cliest.is_active:
            cliest.is_active = False
            cliest.save(update_fields=['is_active'])
            self.stdout.write(self.style.SUCCESS('Tipo CLIEST desativado (is_active=False).'))
        else:
            self.stdout.write('Tipo CLIEST já estava inativo.')
