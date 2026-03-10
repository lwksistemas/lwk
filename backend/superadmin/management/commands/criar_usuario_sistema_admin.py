from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from superadmin.models import UsuarioSistema


class Command(BaseCommand):
    help = 'Cria UsuarioSistema para o superusuário admin'

    def handle(self, *args, **options):
        try:
            admin = User.objects.get(username='admin')
            
            usuario_sistema, created = UsuarioSistema.objects.get_or_create(
                user=admin,
                defaults={
                    'tipo': 'superadmin',
                    'cpf': '00000000000',
                    'is_active': True,
                    'pode_acessar_todas_lojas': True
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS('✅ UsuarioSistema criado para admin'))
            else:
                self.stdout.write(self.style.WARNING('⚠️ UsuarioSistema já existe'))
            
            self.stdout.write(f'CPF: {usuario_sistema.cpf}')
            self.stdout.write(f'Tipo: {usuario_sistema.tipo}')
            self.stdout.write(f'Ativo: {usuario_sistema.is_active}')
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ Usuário admin não encontrado'))
