"""
Comando para limpar dados Asaas órfãos (sem loja correspondente)
"""
from django.core.management.base import BaseCommand
from asaas_integration.deletion_service import AsaasDeletionService
from asaas_integration.models import LojaAssinatura
from superadmin.models import Loja, FinanceiroLoja, PagamentoLoja
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Limpa dados Asaas órfãos (assinaturas sem loja correspondente)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra o que seria removido, sem remover',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 MODO DRY-RUN - Nenhum dado será removido\n'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  MODO REAL - Dados serão removidos!\n'))
        
        self.stdout.write('🧹 Iniciando limpeza de dados órfãos...\n')
        
        # 1. Limpar assinaturas Asaas órfãs
        self.cleanup_asaas_subscriptions(dry_run)
        
        # 2. Limpar financeiros órfãos
        self.cleanup_orphaned_financeiros(dry_run)
        
        # 3. Limpar pagamentos órfãos
        self.cleanup_orphaned_pagamentos(dry_run)
        
        self.stdout.write(self.style.SUCCESS('\n✅ Limpeza concluída!'))

    def cleanup_asaas_subscriptions(self, dry_run):
        """Limpa assinaturas Asaas sem loja correspondente"""
        self.stdout.write('\n📋 Verificando assinaturas Asaas órfãs...')
        
        orphaned_subscriptions = []
        for subscription in LojaAssinatura.objects.all():
            try:
                Loja.objects.get(slug=subscription.loja_slug, is_active=True)
            except Loja.DoesNotExist:
                orphaned_subscriptions.append(subscription)
        
        if not orphaned_subscriptions:
            self.stdout.write(self.style.SUCCESS('  ✅ Nenhuma assinatura órfã encontrada'))
            return
        
        self.stdout.write(self.style.WARNING(f'  ⚠️  Encontradas {len(orphaned_subscriptions)} assinaturas órfãs:'))
        
        for subscription in orphaned_subscriptions:
            self.stdout.write(f'    - Loja: {subscription.loja_slug}')
            self.stdout.write(f'      Cliente Asaas: {subscription.asaas_customer.asaas_id if subscription.asaas_customer else "N/A"}')
            self.stdout.write(f'      Plano: {subscription.plano.nome if subscription.plano else "N/A"}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'\n  🔍 DRY-RUN: {len(orphaned_subscriptions)} assinaturas seriam removidas'))
            return
        
        # Remover assinaturas órfãs
        deletion_service = AsaasDeletionService()
        
        if not deletion_service.available:
            self.stdout.write(self.style.WARNING('  ⚠️  Serviço Asaas não disponível - removendo apenas dados locais'))
        
        removed_count = 0
        for subscription in orphaned_subscriptions:
            try:
                loja_slug = subscription.loja_slug
                
                # Tentar remover do Asaas
                if deletion_service.available:
                    result = deletion_service.delete_loja_from_asaas(loja_slug)
                    if result.get('success'):
                        self.stdout.write(f'    ✅ Dados Asaas removidos: {loja_slug}')
                        self.stdout.write(f'       - Pagamentos cancelados: {result.get("deleted_payments", 0)}')
                        self.stdout.write(f'       - Cliente removido: {result.get("deleted_customer", False)}')
                    else:
                        self.stdout.write(f'    ⚠️  Erro ao remover do Asaas: {result.get("error", "Erro desconhecido")}')
                
                # Remover dados locais
                subscription.delete()
                removed_count += 1
                self.stdout.write(f'    ✅ Assinatura local removida: {loja_slug}')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    ❌ Erro ao remover {subscription.loja_slug}: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n  ✅ {removed_count} assinaturas órfãs removidas'))

    def cleanup_orphaned_financeiros(self, dry_run):
        """Limpa financeiros sem loja correspondente"""
        self.stdout.write('\n📋 Verificando financeiros órfãos...')
        
        orphaned_financeiros = []
        for financeiro in FinanceiroLoja.objects.all():
            try:
                # Verificar se a loja existe
                if not hasattr(financeiro, 'loja') or not financeiro.loja:
                    orphaned_financeiros.append(financeiro)
                elif not Loja.objects.filter(id=financeiro.loja.id, is_active=True).exists():
                    orphaned_financeiros.append(financeiro)
            except Exception:
                orphaned_financeiros.append(financeiro)
        
        if not orphaned_financeiros:
            self.stdout.write(self.style.SUCCESS('  ✅ Nenhum financeiro órfão encontrado'))
            return
        
        self.stdout.write(self.style.WARNING(f'  ⚠️  Encontrados {len(orphaned_financeiros)} financeiros órfãos'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'  🔍 DRY-RUN: {len(orphaned_financeiros)} financeiros seriam removidos'))
            return
        
        # Remover financeiros órfãos
        removed_count = 0
        for financeiro in orphaned_financeiros:
            try:
                financeiro.delete()
                removed_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    ❌ Erro ao remover financeiro {financeiro.id}: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ {removed_count} financeiros órfãos removidos'))

    def cleanup_orphaned_pagamentos(self, dry_run):
        """Limpa pagamentos sem loja correspondente"""
        self.stdout.write('\n📋 Verificando pagamentos órfãos...')
        
        orphaned_pagamentos = []
        for pagamento in PagamentoLoja.objects.all():
            try:
                # Verificar se a loja existe
                if not hasattr(pagamento, 'loja') or not pagamento.loja:
                    orphaned_pagamentos.append(pagamento)
                elif not Loja.objects.filter(id=pagamento.loja.id, is_active=True).exists():
                    orphaned_pagamentos.append(pagamento)
            except Exception:
                orphaned_pagamentos.append(pagamento)
        
        if not orphaned_pagamentos:
            self.stdout.write(self.style.SUCCESS('  ✅ Nenhum pagamento órfão encontrado'))
            return
        
        self.stdout.write(self.style.WARNING(f'  ⚠️  Encontrados {len(orphaned_pagamentos)} pagamentos órfãos'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'  🔍 DRY-RUN: {len(orphaned_pagamentos)} pagamentos seriam removidos'))
            return
        
        # Remover pagamentos órfãos
        removed_count = 0
        for pagamento in orphaned_pagamentos:
            try:
                pagamento.delete()
                removed_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    ❌ Erro ao remover pagamento {pagamento.id}: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ {removed_count} pagamentos órfãos removidos'))
