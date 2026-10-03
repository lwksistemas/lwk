import os
import secrets
import string

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from superadmin.models import UsuarioSistema


def _gerar_senha(tamanho: int = 20) -> str:
    """Gera uma senha aleatória forte."""
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    return "".join(secrets.choice(alphabet) for _ in range(tamanho))


class Command(BaseCommand):
    help = (
        "Cria ou atualiza o usuário super admin. "
        "As credenciais vêm de --username/--email/--password ou das variáveis "
        "de ambiente SUPERADMIN_USERNAME/SUPERADMIN_EMAIL/SUPERADMIN_PASSWORD. "
        "Se nenhuma senha for informada, uma senha aleatória forte é gerada e exibida uma única vez."
    )

    def add_arguments(self, parser):
        parser.add_argument("--username", help="Usuário (padrão: env SUPERADMIN_USERNAME ou 'admin')")
        parser.add_argument("--email", help="E-mail (padrão: env SUPERADMIN_EMAIL)")
        parser.add_argument(
            "--password",
            help="Senha (padrão: env SUPERADMIN_PASSWORD; se ausente, uma senha aleatória é gerada)",
        )
        parser.add_argument("--cpf", help="CPF (padrão: env SUPERADMIN_CPF)")

    def handle(self, *args, **options):
        username = options.get("username") or os.environ.get("SUPERADMIN_USERNAME") or "admin"
        email = options.get("email") or os.environ.get("SUPERADMIN_EMAIL") or "admin@lwksistemas.com.br"
        cpf = options.get("cpf") or os.environ.get("SUPERADMIN_CPF") or "000.000.000-00"

        password = options.get("password") or os.environ.get("SUPERADMIN_PASSWORD")
        senha_gerada = False
        if not password:
            password = _gerar_senha()
            senha_gerada = True

        if len(password) < 12:
            raise CommandError("A senha do superadmin deve ter pelo menos 12 caracteres.")

        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f"✅ Senha do usuário {username} atualizada!"))
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_superuser=True,
                is_staff=True,
                first_name="Administrador",
                last_name="Sistema",
            )
            UsuarioSistema.objects.create(
                user=user,
                tipo="superadmin",
                cpf=cpf,
                telefone="",
                pode_criar_lojas=True,
                pode_gerenciar_financeiro=True,
                pode_acessar_todas_lojas=True,
                senha_foi_alterada=True,
                is_active=True,
            )
            self.stdout.write(self.style.SUCCESS("✅ Super Admin criado com sucesso!"))

        self.stdout.write(self.style.SUCCESS(""))
        self.stdout.write(self.style.SUCCESS("🔐 DADOS DE ACESSO:"))
        self.stdout.write(self.style.SUCCESS("   URL: https://lwksistemas.com.br/superadmin/login"))
        self.stdout.write(self.style.SUCCESS(f"   Usuário: {username}"))
        if senha_gerada:
            # Senha aleatória: exibida uma única vez para o operador anotar.
            self.stdout.write(self.style.WARNING(f"   Senha (gerada, anote agora): {password}"))
        else:
            self.stdout.write(self.style.SUCCESS("   Senha: (definida via argumento/variável de ambiente)"))
        self.stdout.write(self.style.SUCCESS(""))
