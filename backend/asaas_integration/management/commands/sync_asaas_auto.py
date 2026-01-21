"""
Comando para sincronização automática de pagamentos Asaas
Atualiza status de pagamentos e financeiro das lojas
"""
from django.core.management.base import BaseCommand
from superadmin.sync_service import AsaasSyncService

class Command(BaseCommand):
    help = 'Sincroniza automaticamente pagamentos Asaas e atualiza financeiro das lojas'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--loja',
            type=str,
            help='Sincronizar apenas uma loja específica (slug)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar logs detalhados',
        )
    
    def handle(self, *args, **options):
        loja_slug = options.get('loja')
        verbose = options.get('verbose')
        
        try:
            sync_service = AsaasSyncService()
            
            if not sync_service.available:
                self.stdout.write(
                    self.style.ERROR('❌ Serviço Asaas não disponível ou não configurado')
                )
                return
            
            if loja_slug:
                # Sincronizar loja específica
                self.stdout.write(f'🔄 Sincronizando loja: {loja_slug}')
                
                try:
                    from superadmin.models import Loja
                    loja = Loja.objects.get(slug=loja_slug, is_active=True)
                    resultado = sync_service.sync_loja_payments(loja)
                    
                    if resultado.get('success'):
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✅ Loja sincronizada: {loja_slug}\n'
                                f'   - Pagamentos atualizados: {resultado.get("pagamentos_atualizados", 0)}\n'
                                f'   - Status: {resultado.get("status", "N/A")}'
                            )
                        )
                        
                        if resultado.get('blocked'):
                            self.stdout.write(
                                self.style.WARNING(f'⚠️ Loja bloqueada: {loja_slug}')
                            )
                        elif resultado.get('unblocked'):
                            self.stdout.write(
                                self.style.SUCCESS(f'🔓 Loja desbloqueada: {loja_slug}')
                            )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'❌ Erro ao sincronizar loja {loja_slug}: {resultado.get("error")}')
                        )
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Erro: {str(e)}')
                    )
            else:
                # Sincronizar todas as lojas
                self.stdout.write('🔄 Sincronizando todas as lojas...')
                
                resultado = sync_service.sync_all_payments()
                
                if resultado.get('success'):
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Sincronização completa:\n'
                            f'   - Total de lojas: {resultado.get("total_lojas", 0)}\n'
                            f'   - Sucessos: {resultado.get("sucessos", 0)}\n'
                            f'   - Erros: {resultado.get("erros", 0)}\n'
                            f'   - Lojas bloqueadas: {resultado.get("bloqueadas", 0)}\n'
                            f'   - Lojas desbloqueadas: {resultado.get("desbloqueadas", 0)}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Erro na sincronização: {resultado.get("error")}')
                    )
            
            # Mostrar estatísticas se verbose
            if verbose:
                stats = sync_service.get_sync_stats()
                self.stdout.write('\n📊 Estatísticas:')
                for key, value in stats.items():
                    if key != 'error':
                        self.stdout.write(f'   - {key}: {value}')
                        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro inesperado: {str(e)}')
            )