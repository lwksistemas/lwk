"""
Comando para limpar registros antigos do histórico de acessos

Uso:
    python manage.py limpar_historico_antigo --dias=90

Boas práticas:
- Mantém apenas registros dos últimos N dias (padrão: 90)
- Executa em lotes para evitar sobrecarga
- Registra estatísticas da limpeza
- Pode ser agendado via cron/scheduler
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from superadmin.models import HistoricoAcessoGlobal


class Command(BaseCommand):
    help = 'Remove registros antigos do histórico de acessos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dias',
            type=int,
            default=90,
            help='Número de dias para manter (padrão: 90)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a limpeza sem deletar registros'
        )

    def handle(self, *args, **options):
        dias = options['dias']
        dry_run = options['dry_run']
        
        # Calcular data limite
        data_limite = timezone.now() - timedelta(days=dias)
        
        self.stdout.write(f"🗑️  Limpando registros anteriores a {data_limite.strftime('%d/%m/%Y')}")
        
        # Contar registros a serem deletados
        registros_antigos = HistoricoAcessoGlobal.objects.filter(
            created_at__lt=data_limite
        )
        total = registros_antigos.count()
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS('✅ Nenhum registro antigo encontrado'))
            return
        
        self.stdout.write(f"📊 Encontrados {total:,} registros para deletar")
        
        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  Modo DRY-RUN: Nenhum registro será deletado'))
            
            # Mostrar estatísticas
            stats = {
                'logins': registros_antigos.filter(acao='login').count(),
                'criar': registros_antigos.filter(acao='criar').count(),
                'editar': registros_antigos.filter(acao='editar').count(),
                'excluir': registros_antigos.filter(acao='excluir').count(),
                'erros': registros_antigos.filter(sucesso=False).count(),
            }
            
            self.stdout.write('\n📈 Estatísticas dos registros a serem deletados:')
            for acao, count in stats.items():
                self.stdout.write(f"  - {acao}: {count:,}")
            
            return
        
        # Deletar em lotes (para evitar sobrecarga)
        batch_size = 1000
        deleted_total = 0
        
        while True:
            # Obter IDs do próximo lote
            ids = list(
                HistoricoAcessoGlobal.objects.filter(
                    created_at__lt=data_limite
                ).values_list('id', flat=True)[:batch_size]
            )
            
            if not ids:
                break
            
            # Deletar lote
            deleted = HistoricoAcessoGlobal.objects.filter(id__in=ids).delete()[0]
            deleted_total += deleted
            
            self.stdout.write(f"  Deletados {deleted_total:,} de {total:,} registros...")
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Limpeza concluída! {deleted_total:,} registros deletados')
        )
