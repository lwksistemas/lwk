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
        
        # Buscar todas as lojas ativas
        lojas_ativas_ids = list(Loja.objects.filter(is_active=True).values_list('id', flat=True))
        self.stdout.write(f'📋 Lojas ativas: {len(lojas_ativas_ids)}\n')
        
        # Limpar financeiros órfãos ou de lojas inativas
        financeiros_removidos = 0
        for financeiro in FinanceiroLoja.objects.all():
            try:
                # Verificar se a loja existe e está ativa
                if not hasattr(financeiro, 'loja') or not financeiro.loja:
                    self.stdout.write(f'  🗑️  Removendo financeiro órfão ID: {financeiro.id}')
                    financeiro.delete()
                    financeiros_removidos += 1
                elif financeiro.loja.id not in lojas_ativas_ids:
                    loja_nome = financeiro.loja.nome if financeiro.loja else 'Desconhecida'
                    self.stdout.write(f'  🗑️  Removendo financeiro de loja inativa: {loja_nome}')
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
        
        # Limpar pagamentos órfãos ou de lojas inativas
        pagamentos_removidos = 0
        for pagamento in PagamentoLoja.objects.all():
            try:
                # Verificar se a loja existe e está ativa
                if not hasattr(pagamento, 'loja') or not pagamento.loja:
                    self.stdout.write(f'  🗑️  Removendo pagamento órfão ID: {pagamento.id}')
                    pagamento.delete()
                    pagamentos_removidos += 1
                elif pagamento.loja.id not in lojas_ativas_ids:
                    loja_nome = pagamento.loja.nome if pagamento.loja else 'Desconhecida'
                    self.stdout.write(f'  🗑️  Removendo pagamento de loja inativa: {loja_nome} (R$ {pagamento.valor})')
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
