"""Sincroniza AsaasConfig a partir de ASAAS_API_KEY quando a chave no banco é inválida."""
from django.core.management.base import BaseCommand

from asaas_integration.models import AsaasConfig


class Command(BaseCommand):
    help = 'Corrige chave Asaas inválida no banco usando ASAAS_API_KEY do ambiente'

    def handle(self, *args, **options):
        from django.conf import settings

        config = AsaasConfig.get_config()
        db_key = config.api_key_decrypted
        env_key = (getattr(settings, 'ASAAS_API_KEY', None) or '').strip()

        self.stdout.write(f'Banco válido: {AsaasConfig.is_valid_api_key(db_key)}')
        self.stdout.write(f'Env válido: {AsaasConfig.is_valid_api_key(env_key)}')

        if not AsaasConfig.is_valid_api_key(env_key):
            self.stderr.write(self.style.ERROR('ASAAS_API_KEY no ambiente está ausente ou inválida.'))
            return

        if AsaasConfig.is_valid_api_key(db_key) and db_key == env_key:
            self.stdout.write(self.style.SUCCESS('Chave no banco já está correta.'))
            return

        config.api_key = env_key
        config.enabled = bool(getattr(settings, 'ASAAS_INTEGRATION_ENABLED', True))
        config.save()
        self.stdout.write(self.style.SUCCESS(
            f'Chave sincronizada. Ambiente: {"Sandbox" if AsaasConfig.effective_sandbox(env_key) else "Produção"}'
        ))
