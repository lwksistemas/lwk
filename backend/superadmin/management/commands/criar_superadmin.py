from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from superadmin.models import UsuarioSistema


class Command(BaseCommand):
    help = 'Cria um usuário super admin'

    def handle(self, *args, **options):
        username = 'admin'
        email = 'admin@lwksistemas.com.br'
        password = 'Admin@2026'
        cpf = '000.000.000-00'
        
        # Verificar se já existe
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'❌ Usuário {username} já existe!'))
            user = User.objects.get(username=username)
            # Atualizar senha
            user.set_password(password)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'✅ Senha do usuário {username} atualizada!'))
        else:
            # Criar usuário Django
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_superuser=True,
                is_staff=True,
                first_name='Administrador',
                last_name='Sistema'
            )
            
            # Criar perfil UsuarioSistema
            UsuarioSistema.objects.create(
                user=user,
                tipo='superadmin',
                cpf=cpf,
                telefone='',
                pode_criar_lojas=True,
                pode_gerenciar_financeiro=True,
                pode_acessar_todas_lojas=True,
                senha_foi_alterada=True,
                is_active=True
            )
            
            self.stdout.write(self.style.SUCCESS('✅ Super Admin criado com sucesso!'))
        
        self.stdout.write(self.style.SUCCESS(''))
        self.stdout.write(self.style.SUCCESS('🔐 DADOS DE ACESSO:'))
        self.stdout.write(self.style.SUCCESS(f'   URL: https://lwksistemas.com.br/superadmin/login'))
        self.stdout.write(self.style.SUCCESS(f'   Usuário: {username}'))
        self.stdout.write(self.style.SUCCESS(f'   Senha: {password}'))
        self.stdout.write(self.style.SUCCESS(f'   CPF: {cpf}'))
        self.stdout.write(self.style.SUCCESS(''))
