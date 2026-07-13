"""
Management command para criptografar campos sensíveis existentes no banco.

Uso:
    python manage.py encrypt_sensitive_fields
    python manage.py encrypt_sensitive_fields --dry-run
"""
from django.core.management.base import BaseCommand

from core.encryption import encrypt_value, is_encrypted


class Command(BaseCommand):
    help = 'Criptografa campos sensíveis (senhas, API keys) que ainda estão em plaintext'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra o que seria criptografado, sem alterar',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        total_encrypted = 0

        # 1. SuperadminNFSeConfig
        self.stdout.write('\n📦 SuperadminNFSeConfig:')
        total_encrypted += self._encrypt_superadmin_config(dry_run)

        # 2. CRMConfig (todas as lojas)
        self.stdout.write('\n📦 CRMConfig (lojas):')
        total_encrypted += self._encrypt_crm_configs(dry_run)

        # Resumo
        self.stdout.write(f'\n{"=" * 50}')
        if dry_run:
            self.stdout.write(self.style.WARNING(f'🔍 DRY RUN: {total_encrypted} campos seriam criptografados'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ {total_encrypted} campos criptografados com sucesso'))

    def _encrypt_superadmin_config(self, dry_run):
        from asaas_integration.models_nfse_config import SuperadminNFSeConfig
        count = 0

        try:
            config = SuperadminNFSeConfig.get_config()
        except Exception:
            self.stdout.write('  ⚠️  Nenhuma configuração encontrada')
            return 0

        fields = ['issnet_usuario', 'issnet_senha', 'issnet_senha_certificado']
        for field in fields:
            value = getattr(config, field, '') or ''
            if value and not is_encrypted(value):
                if dry_run:
                    self.stdout.write(f'  🔍 {field}: "{value[:3]}***" → seria criptografado')
                else:
                    setattr(config, field, encrypt_value(value))
                    self.stdout.write(f'  🔒 {field}: criptografado')
                count += 1
            elif value and is_encrypted(value):
                self.stdout.write(f'  ✅ {field}: já criptografado')
            else:
                self.stdout.write(f'  ⏭️  {field}: vazio')

        if not dry_run and count > 0:
            config.save()

        return count

    def _encrypt_crm_configs(self, dry_run):
        """Criptografa campos sensíveis em CRMConfig de todas as lojas."""
        from django.conf import settings
        count = 0

        # Buscar todos os bancos de loja
        loja_dbs = [db for db in settings.DATABASES if db.startswith('loja_')]

        if not loja_dbs:
            self.stdout.write('  ⚠️  Nenhum banco de loja encontrado')
            return 0

        for db_name in loja_dbs:
            try:
                from crm_vendas.models_config import CRMConfig
                configs = CRMConfig.objects.using(db_name).all()

                for config in configs:
                    fields = ['issnet_usuario', 'issnet_senha', 'issnet_senha_certificado', 'asaas_api_key']
                    changed = False
                    for field in fields:
                        value = getattr(config, field, '') or ''
                        if value and not is_encrypted(value):
                            if dry_run:
                                self.stdout.write(f'  🔍 [{db_name}] {field}: seria criptografado')
                            else:
                                setattr(config, field, encrypt_value(value))
                                changed = True
                            count += 1

                    if not dry_run and changed:
                        config.save(using=db_name)

            except Exception as e:
                self.stdout.write(f'  ⚠️  [{db_name}] Erro: {e}')

        return count
