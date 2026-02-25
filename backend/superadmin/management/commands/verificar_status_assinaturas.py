"""
Django management command para verificar e atualizar status de assinaturas

✅ NOVO v719: Comando para gerenciamento automático de status

Verifica assinaturas vencidas e atualiza status:
- Vencidas há 7+ dias: status 'atrasado'
- Vencidas há 30+ dias: status 'bloqueado'

Uso:
    python manage.py verificar_status_assinaturas
    python manage.py verificar_status_assinaturas --dry-run
    python manage.py verificar_status_assinaturas --verbose
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from superadmin.models import FinanceiroLoja
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Verifica e atualiza status de assinaturas baseado em vencimento'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a execução sem fazer alterações no banco'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Exibe informações detalhadas de cada loja'
        )
        parser.add_argument(
            '--dias-atraso',
            type=int,
            default=7,
            help='Dias de atraso para marcar como atrasado (padrão: 7)'
        )
        parser.add_argument(
            '--dias-bloqueio',
            type=int,
            default=30,
            help='Dias de atraso para bloquear (padrão: 30)'
        )
    
    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        verbose = options.get('verbose', False)
        dias_atraso = options.get('dias_atraso', 7)
        dias_bloqueio = options.get('dias_bloqueio', 30)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 Modo DRY-RUN ativado - nenhuma alteração será feita\n'))
        
        self.stdout.write(self.style.SUCCESS('🔄 Verificando status de assinaturas...'))
        self.stdout.write(f'   Dias para marcar como atrasado: {dias_atraso}')
        self.stdout.write(f'   Dias para bloquear: {dias_bloqueio}\n')
        
        hoje = timezone.now().date()
        
        # Contadores
        total_verificadas = 0
        marcadas_atrasado = 0
        marcadas_bloqueado = 0
        
        # 1. Verificar assinaturas ativas que venceram (marcar como atrasado)
        self.stdout.write('📋 Verificando assinaturas ativas vencidas...')
        
        data_limite_atraso = hoje - timedelta(days=dias_atraso)
        
        ativas_vencidas = FinanceiroLoja.objects.filter(
            status_pagamento='ativo',
            data_proxima_cobranca__lt=data_limite_atraso
        ).select_related('loja')
        
        total_verificadas += ativas_vencidas.count()
        
        for financeiro in ativas_vencidas:
            loja = financeiro.loja
            dias_vencido = (hoje - financeiro.data_proxima_cobranca).days
            
            if verbose or dry_run:
                self.stdout.write(f'   ⚠️ Loja: {loja.nome} ({loja.slug})')
                self.stdout.write(f'      Status atual: {financeiro.get_status_pagamento_display()}')
                self.stdout.write(f'      Vencimento: {financeiro.data_proxima_cobranca}')
                self.stdout.write(f'      Dias vencido: {dias_vencido}')
                self.stdout.write(f'      Ação: Marcar como ATRASADO')
            
            if not dry_run:
                financeiro.status_pagamento = 'atrasado'
                financeiro.save(update_fields=['status_pagamento'])
                logger.info(f"Loja {loja.slug} marcada como atrasada ({dias_vencido} dias)")
            
            marcadas_atrasado += 1
        
        if marcadas_atrasado > 0:
            self.stdout.write(self.style.WARNING(f'   ⚠️ {marcadas_atrasado} loja(s) marcada(s) como atrasada(s)\n'))
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ Nenhuma loja atrasada\n'))
        
        # 2. Verificar assinaturas atrasadas que devem ser bloqueadas
        self.stdout.write('🚫 Verificando assinaturas atrasadas para bloqueio...')
        
        data_limite_bloqueio = hoje - timedelta(days=dias_bloqueio)
        
        atrasadas_para_bloquear = FinanceiroLoja.objects.filter(
            status_pagamento='atrasado',
            data_proxima_cobranca__lt=data_limite_bloqueio
        ).select_related('loja')
        
        total_verificadas += atrasadas_para_bloquear.count()
        
        for financeiro in atrasadas_para_bloquear:
            loja = financeiro.loja
            dias_vencido = (hoje - financeiro.data_proxima_cobranca).days
            
            if verbose or dry_run:
                self.stdout.write(f'   🚫 Loja: {loja.nome} ({loja.slug})')
                self.stdout.write(f'      Status atual: {financeiro.get_status_pagamento_display()}')
                self.stdout.write(f'      Vencimento: {financeiro.data_proxima_cobranca}')
                self.stdout.write(f'      Dias vencido: {dias_vencido}')
                self.stdout.write(f'      Ação: Marcar como BLOQUEADO')
            
            if not dry_run:
                financeiro.status_pagamento = 'bloqueado'
                financeiro.save(update_fields=['status_pagamento'])
                
                # Bloquear loja também (se tiver campo is_blocked)
                if hasattr(loja, 'is_blocked'):
                    loja.is_blocked = True
                    loja.blocked_at = timezone.now()
                    loja.blocked_reason = f'Assinatura vencida há {dias_vencido} dias'
                    loja.days_overdue = dias_vencido
                    loja.save(update_fields=['is_blocked', 'blocked_at', 'blocked_reason', 'days_overdue'])
                
                logger.warning(f"Loja {loja.slug} BLOQUEADA ({dias_vencido} dias de atraso)")
            
            marcadas_bloqueado += 1
        
        if marcadas_bloqueado > 0:
            self.stdout.write(self.style.ERROR(f'   🚫 {marcadas_bloqueado} loja(s) bloqueada(s)\n'))
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ Nenhuma loja para bloquear\n'))
        
        # 3. Estatísticas gerais
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('✅ Verificação concluída!'))
        self.stdout.write(self.style.SUCCESS(f'   Total verificadas: {total_verificadas}'))
        self.stdout.write(self.style.SUCCESS(f'   Marcadas como atrasado: {marcadas_atrasado}'))
        self.stdout.write(self.style.SUCCESS(f'   Marcadas como bloqueado: {marcadas_bloqueado}'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        # Estatísticas por status
        self.stdout.write('\n📊 Estatísticas por status:')
        
        status_counts = {}
        for status_choice in FinanceiroLoja.STATUS_CHOICES:
            status_key = status_choice[0]
            status_label = status_choice[1]
            count = FinanceiroLoja.objects.filter(status_pagamento=status_key).count()
            status_counts[status_label] = count
            
            if count > 0:
                emoji = {
                    'Ativo': '✅',
                    'Pagamento Pendente': '⏳',
                    'Atrasado': '⚠️',
                    'Suspenso': '⏸️',
                    'Cancelado': '❌',
                }.get(status_label, '📋')
                
                self.stdout.write(f'   {emoji} {status_label}: {count}')
        
        # Alertas
        if status_counts.get('Atrasado', 0) > 0:
            self.stdout.write(self.style.WARNING(
                f'\n⚠️ {status_counts["Atrasado"]} loja(s) com pagamento atrasado.'
            ))
        
        if status_counts.get('Bloqueado', 0) > 0:
            self.stdout.write(self.style.ERROR(
                f'🚫 {status_counts.get("Bloqueado", 0)} loja(s) bloqueada(s).'
            ))
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                '\n💡 Execute sem --dry-run para aplicar as alterações'
            ))
