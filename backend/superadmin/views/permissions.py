from rest_framework import permissions

from ..models import ProfissionalUsuario


class IsOwnerOrSuperAdmin(permissions.BasePermission):
    """Permissão para proprietário da loja ou super admin"""

    def has_permission(self, request, view):
        # Superadmin sempre tem permissão
        if request.user and request.user.is_superuser:
            return True

        # Usuário autenticado tem permissão (verificação específica será feita no método)
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # Superadmin sempre tem permissão
        if request.user and request.user.is_superuser:
            return True

        # Verificar se é o proprietário da loja
        if hasattr(obj, "owner") and request.user == obj.owner:
            return True

        # Verificar se é usuário suporte com acesso à loja (UsuarioSistema - usa lojas_acesso M2M)
        if hasattr(obj, "id"):
            from ..models import UsuarioSistema
            if UsuarioSistema.objects.filter(
                user=request.user,
                lojas_acesso=obj,
                is_active=True,
            ).exists():
                return True
            if UsuarioSistema.objects.filter(
                user=request.user,
                pode_acessar_todas_lojas=True,
                is_active=True,
            ).exists():
                return True

        # Profissional (Clínica da Beleza): pode acessar a loja para trocar senha
        if hasattr(obj, "id") and getattr(view, "action", None) == "alterar_senha_primeiro_acesso":
            if ProfissionalUsuario.objects.filter(user=request.user, loja=obj).exists():
                return True
            from ..models import VendedorUsuario
            if VendedorUsuario.objects.filter(user=request.user, loja=obj).exists():
                return True

        # Backup da loja: dono e superadmin já passaram acima.
        # Na clínica só o perfil administrador. Caixa, limpeza, estoque,
        # recepção e profissional não levam o ZIP com prontuários.
        # No CRM o vendedor da própria loja continua podendo.
        if hasattr(obj, "id"):
            from ..models import UsuarioSistema, VendedorUsuario
            action = getattr(view, "action", None)
            if action in ("exportar_backup", "importar_backup", "enviar_backup_agora", "configuracao_backup", "atualizar_configuracao_backup", "historico_backups"):
                vinculo = (
                    ProfissionalUsuario.objects.filter(user=request.user, loja=obj)
                    .only("perfil")
                    .first()
                )
                if vinculo and vinculo.perfil == ProfissionalUsuario.PERFIL_ADMINISTRADOR:
                    return True
                if UsuarioSistema.objects.filter(user=request.user, lojas_acesso=obj, is_active=True).exists():
                    return True
                if VendedorUsuario.objects.filter(user=request.user, loja=obj).exists():
                    return True

        return False


class IsSuperAdmin(permissions.BasePermission):
    """Permissão APENAS para super admins - SEGURANÇA CRÍTICA"""

    def has_permission(self, request, view):
        return request.user and request.user.is_superuser and request.user.is_active
