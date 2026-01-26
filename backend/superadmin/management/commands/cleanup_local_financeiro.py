"""
Comando para limpar dados financeiros locais órfãos
"""
from django.core.management.base import BaseCommand
from superadmin.models import Loja, FinanceiroLoja, PagamentoLoja
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Limpa dados financeiros locais órfãos (sem loja correspondente)'

    def handle(self, *args, **options):
        self.stdout.write('🧹 Limpando dados financeiros órfãos...\n')
        
        # Limpar financeiros órfãos
        financeiros_removidos = 0
        for financeiro in FinanceiroLoja.objects.all():
            try:
                # Verificar se a loja existe
                if not hasattr(financeiro, 'loja') or not financeiro.loja:
                    self.stdout.write(f'  🗑️  Removendo financeiro órfão ID: {financeiro.id}')
                    financeiro.delete()
                    financeiros_removidos += 1
                elif not Loja.objects.filter(id=financeiro.loja.id, is_active=True).exists():
                    self.stdout.write(f'  🗑️  Removendo financeiro de loja inativa: {financeiro.loja.nome}')
                    financeiro.delete()
                    financeiros_removidos += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Erro ao verificar financeiro {financeiro.id}: {e}'))
                # Tentar remover mesmo assim
                try:
                    financeiro.delete()
                    financeiros_removidos += 1
                except:
                    pass
        
        # Limpar pagamentos órfãos
        pagamentos_removidos = 0
        for pagamento in PagamentoLoja.objects.all():
            try:
                # Verificar se a loja existe
                if not hasattr(pagamento, 'loja') or not pagamento.loja:
                    self.stdout.write(f'  🗑️  Removendo pagamento órfão ID: {pagamento.id}')
                    pagamento.delete()
                    pagamentos_removidos += 1
                elif not Loja.objects.filter(id=pagamento.loja.id, is_active=True).exists():
                    self.stdout.write(f'  🗑️  Removendo pagamento de loja inativa: {pagamento.loja.nome}')
                    pagamento.delete()
                    pagamentos_removidos += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Erro ao verificar pagamento {pagamento.id}: {e}'))
                # Tentar remover mesmo assim
                try:
                    pagamento.delete()
                    pagamentos_removidos += 1
                except:
                    pass
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Limpeza concluída!'))
        self.stdout.write(self.style.SUCCESS(f'  - Financeiros removidos: {financeiros_removidos}'))
        self.stdout.write(self.style.SUCCESS(f'  - Pagamentos removidos: {pagamentos_removidos}'))
