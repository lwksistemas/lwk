"""
Busca um usuário pelo username e mostra vínculos (lojas, UsuarioSistema, ProfissionalUsuario).
Útil para descobrir quem está usando um username quando dá "duplicate key auth_user_username_key".

Uso:
  python manage.py buscar_usuario felix
  python manage.py buscar_usuario felix --remover   # Remove o usuário se não for dono de nenhuma loja
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Busca usuário por username e mostra vínculos (lojas, UsuarioSistema, ProfissionalUsuario)"

    def add_arguments(self, parser):
        parser.add_argument("username", type=str, help="Username a buscar (ex: felix)")
        parser.add_argument(
            "--remover",
            action="store_true",
            help="Remove o usuário se não for owner de nenhuma loja (usuário órfão)",
        )

    def handle(self, *args, **options):
        username = (options["username"] or "").strip()
        remover = options["remover"]

        if not username:
            self.stdout.write(self.style.ERROR("Informe o username. Ex: python manage.py buscar_usuario felix"))
            return

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"Usuário com username '{username}' não encontrado."))
            return

        # Contar vínculos
        from superadmin.models import Loja, UsuarioSistema, ProfissionalUsuario

        lojas_owned = Loja.objects.filter(owner=user)
        n_lojas = lojas_owned.count()
        try:
            usuario_sistema = UsuarioSistema.objects.get(user=user)
            tem_usuario_sistema = True
        except UsuarioSistema.DoesNotExist:
            usuario_sistema = None
            tem_usuario_sistema = False
        n_prof_usuario = ProfissionalUsuario.objects.filter(user=user).count()

        self.stdout.write(self.style.SUCCESS(f"\n=== Usuário: {user.username} ===\n"))
        self.stdout.write(f"  ID: {user.id}")
        self.stdout.write(f"  Email: {user.email or '(vazio)'}")
        self.stdout.write(f"  Nome: {user.get_full_name() or '(vazio)'}")
        self.stdout.write(f"  is_staff: {user.is_staff}  is_superuser: {user.is_superuser}")
        self.stdout.write(f"  date_joined: {user.date_joined}")
        self.stdout.write("")
        self.stdout.write("  Vínculos:")
        self.stdout.write(f"    - Lojas como owner: {n_lojas}")
        if n_lojas > 0:
            for loja in lojas_owned[:5]:
                self.stdout.write(f"        • {loja.nome} (slug: {loja.slug}, id: {loja.id})")
            if n_lojas > 5:
                self.stdout.write(f"        ... e mais {n_lojas - 5}")
        self.stdout.write(f"    - UsuarioSistema (superadmin/suporte): {'Sim' if tem_usuario_sistema else 'Não'}")
        if usuario_sistema:
            self.stdout.write(f"        tipo: {usuario_sistema.tipo}")
        self.stdout.write(f"    - ProfissionalUsuario (vínculos loja+professional): {n_prof_usuario}")
        self.stdout.write("")

        if remover:
            if n_lojas > 0:
                self.stdout.write(
                    self.style.ERROR(f"Não é possível remover: o usuário é owner de {n_lojas} loja(s).")
                )
                return
            if tem_usuario_sistema:
                self.stdout.write(self.style.WARNING("Atenção: usuário possui perfil no sistema (superadmin/suporte). Será removido junto."))
            self.stdout.write(self.style.WARNING(f"Removendo usuário '{username}' (id={user.id})..."))
            user.delete()
            self.stdout.write(self.style.SUCCESS("Usuário removido. Agora você pode criar uma nova loja com esse username."))
        else:
            if n_lojas == 0 and not tem_usuario_sistema:
                self.stdout.write(
                    self.style.WARNING("Este usuário não é owner de nenhuma loja. Para removê-lo e liberar o username, use: --remover")
                )
