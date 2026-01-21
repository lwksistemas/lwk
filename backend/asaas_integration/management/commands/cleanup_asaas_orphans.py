"""
Comando para limpeza de dados Asaas órfãos
Remove dados do Asaas que não têm loja correspondente
"""
from django.core.management.base import BaseCommand
from asaas_integration.deletion_service import AsaasDeletionService

class Command(BaseCommand):
    help = 'Limpa dados Asaas órfãos (sem loja correspondente)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra o que seria excluído, sem executar',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('🔍 Modo DRY-RUN: Apenas mostrando o que seria excluído')
            )
        
        try:
            deletion_service = AsaasDeletionService()
            
            if not deletion_service.available:
                self.stdout.write(
                    self.style.ERROR('❌ Serviço Asaas não disponível ou não configurado')
                )
                return
            
            if dry_run:
                # Simular limpeza
                from asaas_integration.models import LojaAssinatura
                from superadmin.models import Loja
                
                orphaned_count = 0
                for subscription in LojaAssinatura.objects.all():
                    try:
                        Loja.objects.get(slug=subscription.loja_slug, is_active=True)
                    except Loja.DoesNotExist:
                        orphaned_count += 1
                        self.stdout.write(f"🗑️ Seria excluída: {subscription.loja_slug}")
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {orphaned_count} assinaturas órfãs encontradas')
                )
            else:
                # Executar limpeza
                self.stdout.write('🧹 Iniciando limpeza de dados Asaas órfãos...')
                
                result = deletion_service.cleanup_orphaned_asaas_data()
                
                if result.get('success'):
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Limpeza concluída:\n'
                            f'   - Clientes removidos: {result.get("cleaned_customers", 0)}\n'
                            f'   - Pagamentos cancelados: {result.get("cleaned_payments", 0)}\n'
                            f'   - Assinaturas limpas: {result.get("cleaned_subscriptions", 0)}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Erro na limpeza: {result.get("error")}')
                    )
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro inesperado: {str(e)}')
            )