"""
Comando para limpar cache do dashboard CRM.
Uso: python manage.py limpar_cache_dashboard
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache
from crm_vendas.cache import CRMCacheManager


class Command(BaseCommand):
    help = 'Limpa o cache do dashboard CRM de todas as lojas'

    def handle(self, *args, **options):
        self.stdout.write('🧹 Limpando cache do dashboard CRM...')
        
        try:
            # Limpar cache do dashboard
            pattern = f"{CRMCacheManager.DASHBOARD}:*"
            
            # Redis: deletar por pattern
            try:
                from django_redis import get_redis_connection
                redis_conn = get_redis_connection("default")
                keys = redis_conn.keys(pattern)
                if keys:
                    redis_conn.delete(*keys)
                    self.stdout.write(self.style.SUCCESS(f'✅ {len(keys)} chaves de cache removidas'))
                else:
                    self.stdout.write(self.style.WARNING('⚠️  Nenhuma chave de cache encontrada'))
            except Exception as e:
                # Fallback: limpar cache geral
                self.stdout.write(self.style.WARNING(f'⚠️  Redis não disponível, limpando cache geral: {e}'))
                cache.clear()
                self.stdout.write(self.style.SUCCESS('✅ Cache geral limpo'))
            
            self.stdout.write(self.style.SUCCESS('✅ Cache do dashboard limpo com sucesso!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao limpar cache: {e}'))
            raise
