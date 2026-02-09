"""
Management command para limpar logs antigos

Uso:
    python manage.py cleanup_old_logs
    python manage.py cleanup_old_logs --days 60
    python manage.py cleanup_old_logs --dry-run

Este comando remove logs de acesso com mais de N dias (padrão: 90)
para manter o banco de dados otimizado.
"""
import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from superadmin.models import HistoricoAcessoGlobal

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Remove logs de acesso com mais de N dias (padrão: 90)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Número de dias para manter os logs (padrão: 90)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a limpeza sem remover registros'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.SUCCESS(f'🧹 Iniciando limpeza de logs antigos...'))
        self.stdout.write(f'   Critério: Logs com mais de {days} dias')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('   Modo: DRY RUN (simulação)'))
        
        # Calcular data de corte
        cutoff_date = timezone.now() - timedelta(days=days)
        self.stdout.write(f'   Data de corte: {cutoff_date.strftime("%d/%m/%Y %H:%M:%S")}')
        
        # Contar logs a serem removidos
        logs_to_delete = HistoricoAcessoGlobal.objects.filter(
            created_at__lt=cutoff_date
        )
        total_count = logs_to_delete.count()
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('✅ Nenhum log antigo encontrado!'))
            return
        
        self.stdout.write(f'   Logs a serem removidos: {total_count:,}')
        
        # Estatísticas antes da remoção
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('📊 Estatísticas dos logs a serem removidos:'))
        
        # Por ação
        por_acao = logs_to_delete.values('acao').annotate(
            total=models.Count('id')
        ).order_by('-total')[:5]
        
        self.stdout.write('   Top 5 ações:')
        for item in por_acao:
            self.stdout.write(f'     - {item["acao"]}: {item["total"]:,}')
        
        # Por loja
        por_loja = logs_to_delete.exclude(loja_nome='').values('loja_nome').annotate(
            total=models.Count('id')
        ).order_by('-total')[:5]
        
        if por_loja:
            self.stdout.write('   Top 5 lojas:')
            for item in por_loja:
                self.stdout.write(f'     - {item["loja_nome"]}: {item["total"]:,}')
        
        # Executar remoção
        if not dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('🗑️  Removendo logs...'))
            
            try:
                # Remover em lotes para não sobrecarregar o banco
                batch_size = 10000
                deleted_total = 0
                
                while True:
                    # Buscar IDs do próximo lote
                    ids = list(
                        HistoricoAcessoGlobal.objects.filter(
                            created_at__lt=cutoff_date
                        ).values_list('id', flat=True)[:batch_size]
                    )
                    
                    if not ids:
                        break
                    
                    # Deletar lote
                    deleted_count = HistoricoAcessoGlobal.objects.filter(
                        id__in=ids
                    ).delete()[0]
                    
                    deleted_total += deleted_count
                    self.stdout.write(f'   Removidos: {deleted_total:,} / {total_count:,}')
                
                self.stdout.write('')
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Limpeza concluída! {deleted_total:,} logs removidos.'
                    )
                )
                
                # Log para auditoria
                logger.info(
                    f"Limpeza de logs concluída: {deleted_total} registros removidos "
                    f"(mais de {days} dias)"
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Erro ao remover logs: {e}')
                )
                logger.error(f"Erro na limpeza de logs: {e}", exc_info=True)
                raise
        else:
            self.stdout.write('')
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Simulação concluída! {total_count:,} logs seriam removidos.'
                )
            )
        
        # Estatísticas finais
        if not dry_run:
            remaining = HistoricoAcessoGlobal.objects.count()
            self.stdout.write('')
            self.stdout.write(f'📊 Logs restantes no banco: {remaining:,}')


# Import necessário para agregações
from django.db import models
