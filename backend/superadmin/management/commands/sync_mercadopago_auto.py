"""
Comando para sincronização automática de pagamentos Mercado Pago.
Atualiza status de pagamentos e financeiro das lojas consultando a API do MP.

Para atualização em tempo real no Heroku (como o Asaas), agende no Heroku Scheduler:
  - Comando: cd backend && python manage.py sync_mercadopago_auto
  - Frequência sugerida: a cada 10 minutos (ou a cada hora)
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from superadmin.sync_service import sync_all_mercadopago_payments, sync_loja_payments_mercadopago
from superadmin.models import Loja
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sincroniza pagamentos Mercado Pago (consulta API e atualiza status). Agende no Heroku Scheduler para tempo real.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loja',
            type=str,
            help='Sincronizar apenas uma loja (slug)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Exibir informações detalhadas',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f'=== Sync Mercado Pago iniciado em {timezone.now()} ===')
        )

        loja_slug = options.get('loja')
        verbose = options.get('verbose')

        if loja_slug:
            try:
                loja = Loja.objects.get(slug=loja_slug, is_active=True)
                resultado = sync_loja_payments_mercadopago(loja)
                if resultado.get('success'):
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Loja {loja_slug}: {resultado.get('processed', 0)} pagamento(s) atualizado(s) "
                            f"(verificados: {resultado.get('total_checked', 0)})"
                        )
                    )
                else:
                    self.stdout.write(self.style.ERROR(f"❌ Loja {loja_slug}: {resultado.get('error', 'erro')}"))
            except Loja.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ Loja não encontrada: {loja_slug}"))
        else:
            resultado = sync_all_mercadopago_payments()
            if resultado.get('success'):
                total = resultado.get('total_checked', 0)
                processed = resultado.get('processed', 0)
                if total == 0:
                    self.stdout.write(self.style.WARNING('Nenhum pagamento pendente com Mercado Pago.'))
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Sync MP: {processed} pagamento(s) atualizado(s) de {total} verificados."
                        )
                    )
                if verbose:
                    self.stdout.write(f"   total_checked={total}, processed={processed}")
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ Sync MP: {resultado.get('error', 'erro')}")
                )
                if resultado.get('processed', 0) == 0 and 'não configurado' in str(resultado.get('error', '')).lower():
                    self.stdout.write(
                        self.style.WARNING('Configure Mercado Pago no Superadmin (Mercado Pago) para usar o sync.')
                    )
