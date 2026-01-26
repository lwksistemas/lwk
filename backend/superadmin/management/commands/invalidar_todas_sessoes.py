"""
Comando para invalidar TODAS as sessões ativas
Força todos os usuários a fazer login novamente
"""
from django.core.management.base import BaseCommand
from superadmin.models import UserSession


class Command(BaseCommand):
    help = 'Invalida TODAS as sessões ativas, forçando novo login'

    def handle(self, *args, **options):
        self.stdout.write('🔥 Invalidando TODAS as sessões...')
        
        # Contar sessões antes
        count_before = UserSession.objects.count()
        self.stdout.write(f'📊 Sessões ativas: {count_before}')
        
        # Deletar TODAS as sessões
        UserSession.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS(f'✅ {count_before} sessão(ões) invalidada(s)'))
        self.stdout.write(self.style.SUCCESS('✅ Todos os usuários precisarão fazer login novamente'))
