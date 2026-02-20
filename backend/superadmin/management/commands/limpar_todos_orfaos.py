"""
Verifica e remove todos os órfãos do sistema (usuários + dados com loja_id inexistente).

Uso:
  python manage.py limpar_todos_orfaos              # só listar
  python manage.py limpar_todos_orfaos --remover    # remover dados órfãos (tabelas)
  python manage.py limpar_todos_orfaos --remover-usuarios --confirmar   # remover usuários órfãos também
  python manage.py limpar_todos_orfaos --tudo       # remover dados + usuários órfãos (pede confirmação)
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import Count
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Lista e opcionalmente remove todos os órfãos (dados com loja inexistente e usuários sem loja)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--remover',
            action='store_true',
            help='Remover registros órfãos de tabelas (loja_id inexistente)',
        )
        parser.add_argument(
            '--remover-usuarios',
            action='store_true',
            help='Remover usuários órfãos (não são donos de nenhuma loja)',
        )
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirma remoção de usuários órfãos (obrigatório com --remover-usuarios)',
        )
        parser.add_argument(
            '--tudo',
            action='store_true',
            help='Equivalente a --remover + --remover-usuarios --confirmar (executa limpar_dados e limpar_usuarios)',
        )

    def handle(self, *args, **options):
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write('  LIMPEZA DE ÓRFÃOS NO SISTEMA')
        self.stdout.write('=' * 60)
        self.stdout.write('')

        if options['tudo']:
            options['remover'] = True
            options['remover_usuarios'] = True
            options['confirmar'] = True

        # 1. Dados órfãos (tabelas com loja_id de loja inexistente)
        self.stdout.write('📋 Dados órfãos (registros com loja_id inexistente):')
        self.call_command('verificar_dados_orfaos', remover=options['remover'])
        self.stdout.write('')

        # 2. Usuários órfãos
        self.stdout.write('👤 Usuários órfãos (não são donos de nenhuma loja):')
        orfaos = User.objects.filter(is_superuser=False).annotate(
            n_lojas=Count('lojas_owned')
        ).filter(n_lojas=0)
        n = orfaos.count()
        if n == 0:
            self.stdout.write(self.style.SUCCESS('   Nenhum usuário órfão.'))
        else:
            for u in orfaos[:20]:
                self.stdout.write(f'   - {u.username} ({u.email})')
            if n > 20:
                self.stdout.write(f'   ... e mais {n - 20}')
            if options['remover_usuarios'] and options['confirmar']:
                self.call_command('limpar_usuarios_orfaos', confirmar=True)
            elif options['remover_usuarios']:
                self.stdout.write(self.style.WARNING(
                    '   Use --confirmar para realmente remover (ex.: limpar_todos_orfaos --remover-usuarios --confirmar)'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    '   Para remover: python manage.py limpar_usuarios_orfaos --confirmar'
                ))

        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('Concluído.'))
        self.stdout.write('')

    def call_command(self, name, **kwargs):
        from django.core.management import call_command
        import io
        out = io.StringIO()
        err = io.StringIO()
        try:
            if name == 'verificar_dados_orfaos':
                call_command('verificar_dados_orfaos', remover=kwargs.get('remover', False), stdout=out, stderr=err)
            elif name == 'limpar_usuarios_orfaos':
                call_command('limpar_usuarios_orfaos', confirmar=kwargs.get('confirmar', False), stdout=out, stderr=err)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Erro ao chamar {name}: {e}'))
            return
        for line in out.getvalue().splitlines():
            self.stdout.write('   ' + line)
