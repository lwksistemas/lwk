"""
Comando para limpar cache de estatísticas

Uso:
    python manage.py clear_stats_cache
"""

from django.core.management.base import BaseCommand
from superadmin.cache import CacheService


class Command(BaseCommand):
    help = 'Limpa o cache de estatísticas de auditoria'

    def handle(self, *args, **options):
        self.stdout.write('🧹 Limpando cache de estatísticas...')
        
        try:
            CacheService.clear_all()
            self.stdout.write(self.style.SUCCESS('✅ Cache limpo com sucesso!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao limpar cache: {e}'))
