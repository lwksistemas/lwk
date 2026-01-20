"""
Comando para sincronizar pagamentos com Asaas
Pode ser executado manualmente ou via cron job
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from superadmin.sync_service import AsaasSyncService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sincroniza pagamentos com a API do Asaas e atualiza status das lojas'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--loja',
            type=str,
            help='Sincronizar apenas uma loja específica (slug)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Exibir informações detalhadas',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular execução sem fazer alterações',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f'=== Sincronização Asaas iniciada em {timezone.now()} ===')
        )
        
        sync_service = AsaasSyncService()
        
        if options['loja']:
            # Sincronizar loja específica
            self.sync_single_loja(sync_service, options['loja'], options)
        else:
            # Sincronizar todas as lojas
            self.sync_all_lojas(sync_service, options)
    
    def sync_single_loja(self, sync_service, loja_slug, options):
        """Sincroniza uma loja específica"""
        try:
            from superadmin.models import Loja
            
            loja = Loja.objects.get(slug=loja_slug, is_active=True)
            
            if options['verbose']:
                self.stdout.write(f"Sincronizando loja: {loja.nome}")
            
            if options['dry_run']:
                self.stdout.write(
                    self.style.WARNING('DRY RUN - Nenhuma alteração será feita')
                )
                return
            
            resultado = sync_service.sync_loja_payments(loja)
            
            if resultado['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Loja {loja.nome} sincronizada com sucesso"
                    )
                )
                
                if options['verbose']:
                    self.stdout.write(f"   Pagamentos atualizados: {resultado['pagamentos_atualizados']}")
                    self.stdout.write(f"   Status: {resultado['status']}")
                    
                    if resultado.get('blocked'):
                        self.stdout.write(
                            self.style.ERROR("   🔒 Loja foi BLOQUEADA por inadimplência")
                        )
                    
                    if resultado.get('unblocked'):
                        self.stdout.write(
                            self.style.SUCCESS("   🔓 Loja foi DESBLOQUEADA após pagamento")
                        )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Erro ao sincronizar loja {loja.nome}: {resultado.get('error')}"
                    )
                )
                
        except Loja.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ Loja '{loja_slug}' não encontrada")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Erro inesperado: {e}")
            )
    
    def sync_all_lojas(self, sync_service, options):
        """Sincroniza todas as lojas"""
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('DRY RUN - Nenhuma alteração será feita')
            )
            
            # Mostrar estatísticas apenas
            stats = sync_service.get_sync_stats()
            self.show_stats(stats)
            return
        
        # Executar sincronização completa
        resultado = sync_service.sync_all_payments()
        
        if resultado['success']:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Sincronização completa finalizada"
                )
            )
            
            # Mostrar resumo
            self.stdout.write(f"📊 Total de lojas: {resultado['total_lojas']}")
            self.stdout.write(f"✅ Sucessos: {resultado['sucessos']}")
            self.stdout.write(f"❌ Erros: {resultado['erros']}")
            
            if resultado['bloqueadas'] > 0:
                self.stdout.write(
                    self.style.ERROR(f"🔒 Lojas bloqueadas: {resultado['bloqueadas']}")
                )
            
            if resultado['desbloqueadas'] > 0:
                self.stdout.write(
                    self.style.SUCCESS(f"🔓 Lojas desbloqueadas: {resultado['desbloqueadas']}")
                )
            
            # Mostrar estatísticas atuais
            if options['verbose']:
                stats = sync_service.get_sync_stats()
                self.show_stats(stats)
        else:
            self.stdout.write(
                self.style.ERROR(f"❌ Erro na sincronização: {resultado.get('error')}")
            )
    
    def show_stats(self, stats):
        """Exibe estatísticas do sistema"""
        self.stdout.write("\n=== Estatísticas do Sistema ===")
        self.stdout.write(f"Total de lojas ativas: {stats.get('total_lojas', 0)}")
        self.stdout.write(f"Lojas com Asaas: {stats.get('lojas_com_asaas', 0)}")
        self.stdout.write(f"Lojas bloqueadas: {stats.get('lojas_bloqueadas', 0)}")
        self.stdout.write(f"Pagamentos pendentes: {stats.get('pagamentos_pendentes', 0)}")
        self.stdout.write(f"Pagamentos pagos hoje: {stats.get('pagamentos_pagos_hoje', 0)}")
        
        if stats.get('error'):
            self.stdout.write(
                self.style.ERROR(f"Erro ao obter estatísticas: {stats['error']}")
            )