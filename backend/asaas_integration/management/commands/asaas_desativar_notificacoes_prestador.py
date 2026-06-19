"""Desativa e-mails do Asaas para o prestador (LWK) nos clientes já cadastrados."""
from django.core.management.base import BaseCommand

from asaas_integration.models import AsaasConfig
from asaas_integration.client import AsaasClient
from superadmin.models import FinanceiroLoja


class Command(BaseCommand):
    help = 'Desativa notificações "Para mim" do Asaas nos clientes das lojas (conta LWK)'

    def add_arguments(self, parser):
        parser.add_argument('--slug', help='Slug ou atalho de uma loja específica')

    def handle(self, *args, **options):
        config = AsaasConfig.get_config()
        api_key = AsaasConfig.resolve_api_key()
        if not api_key or not config.enabled:
            self.stderr.write('Asaas não configurado ou desabilitado')
            return

        client = AsaasClient(api_key=api_key, sandbox=config.sandbox)
        qs = FinanceiroLoja.objects.exclude(asaas_customer_id='').select_related('loja')
        slug = (options.get('slug') or '').strip()
        if slug:
            qs = qs.filter(loja__slug=slug) | qs.filter(loja__atalho=slug)

        vistos = set()
        for fin in qs:
            cid = (fin.asaas_customer_id or '').strip()
            if not cid or cid in vistos:
                continue
            vistos.add(cid)
            loja = fin.loja
            self.stdout.write(f'Loja {loja.nome} → customer {cid}')
            client.disable_provider_notifications(cid)

        self.stdout.write(self.style.SUCCESS(f'Concluído — {len(vistos)} cliente(s) Asaas processado(s)'))
