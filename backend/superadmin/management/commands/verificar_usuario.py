"""
Verifica um usuário por username e, se for órfão (não é dono de nenhuma loja),
pode removê-lo para liberar o username ao criar nova loja.

Uso:
  python manage.py verificar_usuario felix              # só mostrar
  python manage.py verificar_usuario felix --remover    # remover se for órfão
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from superadmin.models import Loja, UserSession, ProfissionalUsuario


class Command(BaseCommand):
    help = 'Verifica usuário por username e opcionalmente remove se for órfão (sem lojas)'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username do usuário (ex: felix)')
        parser.add_argument(
            '--remover',
            action='store_true',
            help='Remove o usuário se for órfão (não é dono de nenhuma loja e não é superuser)',
        )

    def handle(self, *args, **options):
        username = (options['username'] or '').strip()
        if not username:
            self.stdout.write(self.style.ERROR('Informe o username. Ex: python manage.py verificar_usuario felix'))
            return

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING(f'Usuário "{username}" não existe no sistema.'))
            self.stdout.write('Você pode criar uma nova loja com esse username sem conflito.')
            return

        lojas = Loja.objects.filter(owner=user)
        n_lojas = lojas.count()
        is_orphan = n_lojas == 0 and not user.is_superuser

        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write(f'👤 Usuário: {user.username}')
        self.stdout.write(f'   ID: {user.id}')
        self.stdout.write(f'   E-mail: {user.email or "(vazio)"}')
        self.stdout.write(f'   Nome: {user.get_full_name() or "(vazio)"}')
        self.stdout.write(f'   Superuser: {"Sim" if user.is_superuser else "Não"}')
        self.stdout.write(f'   Lojas que é dono: {n_lojas}')
        if n_lojas > 0:
            for loja in lojas[:5]:
                self.stdout.write(f'      - {loja.nome} (slug: {loja.slug})')
            if n_lojas > 5:
                self.stdout.write(f'      ... e mais {n_lojas - 5}')
        self.stdout.write('=' * 60)

        if not is_orphan:
            if user.is_superuser:
                self.stdout.write(self.style.WARNING('\n⚠️ Superuser não pode ser removido por este comando.'))
            elif n_lojas > 0:
                self.stdout.write(self.style.WARNING(f'\n⚠️ Este usuário é dono de {n_lojas} loja(s). Remova as lojas primeiro.'))
            return

        self.stdout.write(self.style.WARNING('\n📌 Este usuário é órfão (não é dono de nenhuma loja).'))
        self.stdout.write('   Por isso ao criar uma nova loja com o mesmo username ocorre erro de "duplicate key".')

        if not options['remover']:
            self.stdout.write('')
            self.stdout.write('Para remover este usuário e liberar o username "felix" para uma nova loja, execute:')
            self.stdout.write(self.style.SUCCESS(f'  python manage.py verificar_usuario {username} --remover'))
            self.stdout.write('')
            self.stdout.write('Ou remova todos os órfãos de uma vez:')
            self.stdout.write(self.style.SUCCESS('  python manage.py limpar_usuarios_orfaos --confirmar'))
            return

        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Removendo usuário órfão...'))

        try:
            UserSession.objects.filter(user=user).delete()
            ProfissionalUsuario.objects.filter(user=user).delete()
            user.groups.clear()
            user.user_permissions.clear()
            user.delete()
            self.stdout.write(self.style.SUCCESS(f'✅ Usuário "{username}" removido. Agora você pode criar uma nova loja com esse username.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao remover: {e}'))
