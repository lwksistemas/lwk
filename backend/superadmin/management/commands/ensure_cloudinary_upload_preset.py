"""Atualiza o preset unsigned do Cloudinary para aceitar subpastas por upload."""
from django.core.management.base import BaseCommand

from core.cloudinary_upload_preset import DEFAULT_PRESET, ensure_cloudinary_upload_preset


class Command(BaseCommand):
    help = 'Garante preset Cloudinary sem pasta fixa (permite lwksistemas/superadmin, loja/login, etc.)'

    def add_arguments(self, parser):
        parser.add_argument('--preset', default=DEFAULT_PRESET, help='Nome do upload preset')

    def handle(self, *args, **options):
        preset = options['preset']
        if ensure_cloudinary_upload_preset(preset):
            self.stdout.write(self.style.SUCCESS(f'Preset {preset} OK (pastas dinâmicas).'))
        else:
            self.stdout.write(self.style.ERROR(f'Falha ao atualizar preset {preset}.'))
