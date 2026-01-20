"""
Comando para sincronizar status dos pagamentos com a API do Asaas
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from asaas_integration.models import AsaasPayment
from asaas_integration.client import AsaasPaymentService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sincroniza status dos pagamentos com a API do Asaas'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--payment-id',
            type=str,
            help='ID específico do pagamento para sincronizar'
        )
        parser.add_argument(
            '--pending-only',
            action='store_true',
            help='Sincronizar apenas pagamentos pendentes'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Sincronizar pagamentos dos últimos N dias (padrão: 30)'
        )
    
    def handle(self, *args, **options):
        service = AsaasPaymentService()
        
        # Filtrar pagamentos
        if options['payment_id']:
            payments = AsaasPayment.objects.filter(asaas_id=options['payment_id'])
            self.stdout.write(f"Sincronizando pagamento específico: {options['payment_id']}")
        else:
            # Filtrar por data
            since_date = timezone.now() - timezone.timedelta(days=options['days'])
            payments = AsaasPayment.objects.filter(created_at__gte=since_date)
            
            # Filtrar apenas pendentes se solicitado
            if options['pending_only']:
                payments = payments.filter(status='PENDING')
                self.stdout.write(f"Sincronizando {payments.count()} pagamentos pendentes dos últimos {options['days']} dias")
            else:
                self.stdout.write(f"Sincronizando {payments.count()} pagamentos dos últimos {options['days']} dias")
        
        updated_count = 0
        error_count = 0
        
        for payment in payments:
            try:
                self.stdout.write(f"Sincronizando pagamento {payment.asaas_id}...")
                
                result = service.get_payment_status(payment.asaas_id)
                
                if result['success']:
                    old_status = payment.status
                    payment.status = result['status']
                    
                    if result.get('payment_date'):
                        from datetime import datetime
                        payment.payment_date = datetime.fromisoformat(result['payment_date'].replace('Z', '+00:00'))
                    
                    payment.raw_data = result['raw_payment']
                    payment.save()
                    
                    if old_status != payment.status:
                        self.stdout.write(
                            self.style.SUCCESS(f"✅ Pagamento {payment.asaas_id}: {old_status} → {payment.status}")
                        )
                        updated_count += 1
                    else:
                        self.stdout.write(f"   Status inalterado: {payment.status}")
                else:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Erro ao sincronizar {payment.asaas_id}: {result['error']}")
                    )
                    error_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Erro inesperado ao sincronizar {payment.asaas_id}: {e}")
                )
                error_count += 1
        
        # Resumo
        self.stdout.write("\n" + "="*50)
        self.stdout.write(f"Sincronização concluída:")
        self.stdout.write(f"  • Pagamentos atualizados: {updated_count}")
        self.stdout.write(f"  • Erros: {error_count}")
        self.stdout.write(f"  • Total processado: {payments.count()}")
        
        if updated_count > 0:
            self.stdout.write(self.style.SUCCESS("✅ Sincronização realizada com sucesso!"))
        elif error_count > 0:
            self.stdout.write(self.style.WARNING("⚠️  Sincronização concluída com erros"))
        else:
            self.stdout.write("ℹ️  Nenhuma atualização necessária")