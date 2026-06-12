"""
Registra webhook LWK nas instâncias Evolution já conectadas.
Útil após deploy da confirmação de agendamento (lojas que já tinham QR escaneado).

  python manage.py ensure_evolution_webhooks
  python manage.py ensure_evolution_webhooks --slug novaimagem
"""
from django.core.management.base import BaseCommand

from whatsapp.evolution_client import evolution_configured, evolution_webhook_url, set_instance_webhook
from whatsapp.models import WhatsAppConfig


class Command(BaseCommand):
    help = 'Configura webhook Evolution (MESSAGES_UPSERT) nas lojas WhatsApp Web conectadas.'

    def add_arguments(self, parser):
        parser.add_argument('--slug', type=str, help='Apenas esta loja (slug ou atalho)')

    def handle(self, *args, **options):
        if not evolution_configured():
            self.stderr.write(self.style.ERROR('Evolution API não configurada (EVOLUTION_API_URL / EVOLUTION_API_KEY).'))
            return

        webhook_url = evolution_webhook_url()
        self.stdout.write(f'Webhook URL: {webhook_url}')

        qs = WhatsAppConfig.objects.using('default').filter(
            whatsapp_ativo=True,
            whatsapp_provider=WhatsAppConfig.PROVIDER_EVOLUTION,
            whatsapp_connection_status=WhatsAppConfig.CONNECTION_CONNECTED,
        ).select_related('loja')

        slug = (options.get('slug') or '').strip()
        if slug:
            from superadmin.models import Loja
            loja = Loja.objects.using('default').filter(slug__iexact=slug).first()
            if not loja:
                loja = Loja.objects.using('default').filter(atalho__iexact=slug).first()
            if not loja:
                self.stderr.write(self.style.ERROR(f'Loja não encontrada: {slug}'))
                return
            qs = qs.filter(loja_id=loja.id)

        ok_count = 0
        for config in qs:
            instance = (config.evolution_instance_name or '').strip()
            if not instance:
                from whatsapp.evolution_client import evolution_instance_name
                instance = evolution_instance_name(config.loja_id)
            try:
                set_instance_webhook(instance)
                self.stdout.write(self.style.SUCCESS(f'  ✓ {config.loja.nome} ({instance})'))
                ok_count += 1
            except Exception as exc:
                self.stderr.write(self.style.WARNING(f'  ✗ {config.loja.nome} ({instance}): {exc}'))

        if not ok_count:
            self.stdout.write(self.style.WARNING('Nenhuma instância conectada para configurar.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Concluído: {ok_count} webhook(s) registrado(s).'))
