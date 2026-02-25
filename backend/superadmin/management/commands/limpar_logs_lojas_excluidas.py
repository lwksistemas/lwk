"""
Management command para limpar logs e alertas de lojas excluídas

Uso:
    python manage.py limpar_logs_lojas_excluidas
    python manage.py limpar_logs_lojas_excluidas --dry-run

Este comando remove:
- Logs de acesso (HistoricoAcessoGlobal) de lojas que não existem mais
- Alertas de segurança (ViolacaoSeguranca) de lojas que não existem mais

Útil para limpar dados órfãos de lojas excluídas antes da implementação do v714.
"""
import logging
from django.core.management.base import BaseCommand
from django.db import models, transaction
from superadmin.models import HistoricoAcessoGlobal, ViolacaoSeguranca, Loja

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Remove logs e alertas de lojas que não existem mais no sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a limpeza sem remover registros'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.SUCCESS('🧹 Iniciando limpeza de logs de lojas excluídas...'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('   Modo: DRY RUN (simulação)'))
        
        self.stdout.write('')
        
        # 1. Obter lista de slugs de lojas ativas
        lojas_ativas = set(Loja.objects.values_list('slug', flat=True))
        total_lojas_ativas = len(lojas_ativas)
        
        self.stdout.write(f'📊 Lojas ativas no sistema: {total_lojas_ativas}')
        self.stdout.write('')
        
        # 2. Identificar logs de lojas excluídas
        self.stdout.write(self.style.WARNING('🔍 Analisando logs de acesso...'))
        
        # Logs com loja_slug preenchido (ações dentro da loja)
        logs_com_slug = HistoricoAcessoGlobal.objects.exclude(loja_slug='')
        total_logs_com_slug = logs_com_slug.count()
        
        # Logs de lojas excluídas (slug não está na lista de lojas ativas)
        logs_orfaos_slug = logs_com_slug.exclude(loja_slug__in=lojas_ativas)
        
        # Logs de ações sobre lojas (recurso="Loja") que não existem mais
        # Obter IDs de lojas ativas
        lojas_ativas_ids = set(Loja.objects.values_list('id', flat=True))
        
        logs_orfaos_recurso = HistoricoAcessoGlobal.objects.filter(
            recurso='Loja'
        ).exclude(
            recurso_id__in=lojas_ativas_ids
        ).exclude(
            recurso_id__isnull=True
        )
        
        # Combinar ambos os tipos de logs órfãos (usar Q para OR)
        from django.db.models import Q
        logs_orfaos = HistoricoAcessoGlobal.objects.filter(
            Q(loja_slug__in=logs_orfaos_slug.values_list('loja_slug', flat=True)) |
            Q(id__in=logs_orfaos_recurso.values_list('id', flat=True))
        ).distinct()
        
        total_logs_orfaos = logs_orfaos.count()
        
        self.stdout.write(f'   Total de logs com loja: {total_logs_com_slug:,}')
        self.stdout.write(f'   Logs de ações sobre lojas excluídas: {logs_orfaos_recurso.count():,}')
        self.stdout.write(f'   Logs de ações dentro de lojas excluídas: {logs_orfaos_slug.count():,}')
        self.stdout.write(f'   Total de logs órfãos: {total_logs_orfaos:,}')
        
        # Estatísticas dos logs órfãos
        if total_logs_orfaos > 0:
            self.stdout.write('')
            self.stdout.write('   📋 Tipos de logs órfãos:')
            
            # Por tipo de ação
            por_tipo = logs_orfaos.values('acao', 'recurso').annotate(
                total=models.Count('id')
            ).order_by('-total')[:10]
            
            for item in por_tipo:
                self.stdout.write(f'     - {item["acao"]} {item["recurso"]}: {item["total"]:,}')
            
            self.stdout.write('')
            self.stdout.write('   📋 Top 10 lojas excluídas com mais logs:')
            
            por_loja = logs_orfaos.exclude(loja_nome='').values('loja_slug', 'loja_nome').annotate(
                total=models.Count('id')
            ).order_by('-total')[:10]
            
            for item in por_loja:
                loja_nome = item['loja_nome'] or 'Sem nome'
                loja_slug = item['loja_slug'] or 'Sem slug'
                self.stdout.write(f'     - {loja_slug} ({loja_nome}): {item["total"]:,} logs')
        
        self.stdout.write('')
        
        # 3. Identificar alertas de lojas excluídas
        self.stdout.write(self.style.WARNING('🔍 Analisando alertas de segurança...'))
        
        # Alertas com loja preenchida
        alertas_com_loja = ViolacaoSeguranca.objects.exclude(loja__isnull=True)
        total_alertas_com_loja = alertas_com_loja.count()
        
        # Alertas de lojas excluídas (loja_id não existe mais)
        # Como loja usa SET_NULL, precisamos verificar pelo loja_nome
        alertas_orfaos = ViolacaoSeguranca.objects.filter(
            loja__isnull=True
        ).exclude(loja_nome='')
        total_alertas_orfaos = alertas_orfaos.count()
        
        self.stdout.write(f'   Total de alertas com loja: {total_alertas_com_loja:,}')
        self.stdout.write(f'   Alertas de lojas excluídas: {total_alertas_orfaos:,}')
        
        # Estatísticas dos alertas órfãos
        if total_alertas_orfaos > 0:
            self.stdout.write('')
            self.stdout.write('   📋 Top 10 lojas excluídas com mais alertas:')
            
            por_loja_alerta = alertas_orfaos.values('loja_nome').annotate(
                total=models.Count('id')
            ).order_by('-total')[:10]
            
            for item in por_loja_alerta:
                self.stdout.write(f'     - {item["loja_nome"]}: {item["total"]:,} alertas')
        
        self.stdout.write('')
        
        # 4. Resumo
        total_a_remover = total_logs_orfaos + total_alertas_orfaos
        
        if total_a_remover == 0:
            self.stdout.write(self.style.SUCCESS('✅ Nenhum dado órfão encontrado!'))
            self.stdout.write('   Todos os logs e alertas pertencem a lojas ativas.')
            return
        
        self.stdout.write(self.style.WARNING('📊 RESUMO DA LIMPEZA:'))
        self.stdout.write(f'   Logs a remover: {total_logs_orfaos:,}')
        self.stdout.write(f'   Alertas a remover: {total_alertas_orfaos:,}')
        self.stdout.write(f'   TOTAL: {total_a_remover:,} registros')
        self.stdout.write('')
        
        # 5. Executar remoção
        if not dry_run:
            self.stdout.write(self.style.WARNING('🗑️  Removendo dados órfãos...'))
            
            try:
                deleted_logs = 0
                deleted_alertas = 0
                
                with transaction.atomic():
                    # Remover logs
                    if total_logs_orfaos > 0:
                        self.stdout.write('   Removendo logs...')
                        deleted_logs = logs_orfaos.delete()[0]
                        self.stdout.write(f'   ✅ {deleted_logs:,} logs removidos')
                    
                    # Remover alertas
                    if total_alertas_orfaos > 0:
                        self.stdout.write('   Removendo alertas...')
                        deleted_alertas = alertas_orfaos.delete()[0]
                        self.stdout.write(f'   ✅ {deleted_alertas:,} alertas removidos')
                
                self.stdout.write('')
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Limpeza concluída! {total_a_remover:,} registros removidos.'
                    )
                )
                
                # Log para auditoria
                logger.info(
                    f"Limpeza de logs de lojas excluídas concluída: "
                    f"{deleted_logs} logs + {deleted_alertas} alertas removidos"
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Erro ao remover dados: {e}')
                )
                logger.error(f"Erro na limpeza de logs de lojas excluídas: {e}", exc_info=True)
                raise
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Simulação concluída! {total_a_remover:,} registros seriam removidos.'
                )
            )
        
        # 6. Estatísticas finais
        if not dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('📊 ESTATÍSTICAS FINAIS:'))
            
            total_logs = HistoricoAcessoGlobal.objects.count()
            logs_com_loja_ativa = HistoricoAcessoGlobal.objects.filter(
                loja_slug__in=lojas_ativas
            ).count()
            logs_sem_loja = HistoricoAcessoGlobal.objects.filter(loja_slug='').count()
            
            self.stdout.write(f'   Total de logs: {total_logs:,}')
            self.stdout.write(f'   Logs de lojas ativas: {logs_com_loja_ativa:,}')
            self.stdout.write(f'   Logs sem loja (SuperAdmin): {logs_sem_loja:,}')
            
            total_alertas = ViolacaoSeguranca.objects.count()
            alertas_com_loja_ativa = ViolacaoSeguranca.objects.filter(
                loja__isnull=False
            ).count()
            alertas_sem_loja = ViolacaoSeguranca.objects.filter(
                loja__isnull=True,
                loja_nome=''
            ).count()
            
            self.stdout.write('')
            self.stdout.write(f'   Total de alertas: {total_alertas:,}')
            self.stdout.write(f'   Alertas de lojas ativas: {alertas_com_loja_ativa:,}')
            self.stdout.write(f'   Alertas sem loja (SuperAdmin): {alertas_sem_loja:,}')
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('✅ Banco de dados limpo e otimizado!'))
