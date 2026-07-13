"""
Configura API Key Asaas no CRM Vendas de uma loja (boleto de comissão / NFS-e).

Uso:
  python manage.py configurar_asaas_crm_loja felix --api-key '$aact_prod_...'
  python manage.py configurar_asaas_crm_loja felix --test
"""
from django.core.management.base import BaseCommand, CommandError

from core.db_config import ensure_loja_database_config
from crm_vendas.crm_config_helpers import get_crm_config_for_loja
from superadmin.loja_utils import resolve_loja_by_slug_or_atalho
from tenants.middleware import set_current_loja_id, set_current_tenant_db


class Command(BaseCommand):
    help = 'Atualiza API Key Asaas no CRMConfig da loja (atalho ou slug).'

    def add_arguments(self, parser):
        parser.add_argument('loja', type=str, help='Atalho ou slug da loja (ex: felix)')
        parser.add_argument('--api-key', type=str, default='', help='Chave API v3 Asaas da conta da loja')
        parser.add_argument('--sandbox', action='store_true', help='Forçar ambiente sandbox')
        parser.add_argument('--producao', action='store_true', help='Forçar ambiente produção')
        parser.add_argument('--test', action='store_true', help='Testar chave salva ou informada')

    def handle(self, *args, **options):
        loja_ref = options['loja'].strip()
        loja = resolve_loja_by_slug_or_atalho(loja_ref)
        if not loja:
            raise CommandError(f'Loja não encontrada: {loja_ref}')

        set_current_loja_id(loja.id)
        db_name = loja.database_name or f'loja_{loja.slug}'
        if not ensure_loja_database_config(db_name, conn_max_age=0):
            raise CommandError(f'Falha ao configurar banco {db_name}')
        set_current_tenant_db(db_name)
        cfg = get_crm_config_for_loja(loja.id)

        from asaas_integration.api_key_utils import (
            asaas_key_is_sandbox,
            is_valid_asaas_api_key,
            normalize_asaas_api_key,
        )

        api_key = normalize_asaas_api_key((options.get('api_key') or '').strip())
        if api_key:
            if not is_valid_asaas_api_key(api_key):
                raise CommandError(
                    'Chave API inválida. Use $aact_prod_... (produção) ou $aact_hmlg_... (sandbox).'
                )
            cfg.asaas_api_key = api_key
            if options['sandbox']:
                cfg.asaas_sandbox = True
            elif options['producao']:
                cfg.asaas_sandbox = False
            else:
                cfg.asaas_sandbox = asaas_key_is_sandbox(api_key)
            cfg.save(update_fields=['asaas_api_key', 'asaas_sandbox', 'updated_at'])
            self.stdout.write(self.style.SUCCESS(
                f'API Key Asaas salva para {loja.nome} (sandbox={cfg.asaas_sandbox})'
            ))

        if options['test']:
            key = api_key or normalize_asaas_api_key((cfg.asaas_api_key or '').strip())
            if not key:
                raise CommandError('Nenhuma API Key configurada. Use --api-key ou configure antes.')
            sandbox = cfg.asaas_sandbox
            from asaas_integration.client import AsaasClient
            client = AsaasClient(api_key=key, sandbox=sandbox)
            client._make_request('GET', 'customers?limit=1')
            env = 'sandbox' if sandbox else 'produção'
            self.stdout.write(self.style.SUCCESS(f'Conexão Asaas OK ({env})'))
            return

        if not api_key:
            configured = bool((cfg.asaas_api_key or '').strip())
            self.stdout.write(
                f'Loja: {loja.nome} (atalho={loja.atalho}, slug={loja.slug})\n'
                f'API Key configurada: {configured}\n'
                f'Sandbox: {cfg.asaas_sandbox}\n'
                f'Webhook: https://api.lwksistemas.com.br/api/crm-vendas/webhooks/asaas/{loja.atalho or loja.slug}/'
            )
