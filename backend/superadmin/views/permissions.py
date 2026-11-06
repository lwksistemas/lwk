import logging

from rest_framework import permissions

from ..models import ProfissionalUsuario

logger = logging.getLogger(__name__)

_ACOES_BACKUP_DA_LOJA = (
    "exportar_backup",
    "enviar_backup_agora",
    "configuracao_backup",
    "atualizar_configuracao_backup",
    "historico_backups",
)


def _vendedor_crm_e_admin(user, loja) -> bool:
    """True só quando o login é o vendedor administrador da loja.

    Sem essa leitura, ou se ela falhar, o vendedor comum não leva o ZIP.
    O contexto da loja volta ao que estava antes da consulta.
    """
    from ..models import VendedorUsuario

    vinculo = (
        VendedorUsuario.objects.filter(user=user, loja=loja)
        .only("vendedor_id")
        .first()
    )
    if not vinculo or not getattr(vinculo, "vendedor_id", None):
        return False

    from tenants.middleware import (
        get_current_loja_id,
        get_current_tenant_db,
        set_current_loja_id,
        set_current_tenant_db,
    )

    anterior_db = get_current_tenant_db()
    anterior_loja = get_current_loja_id()
    try:
        from core.db_config import ensure_loja_database_config
        from crm_vendas.models import Vendedor

        db_name = getattr(loja, "database_name", None) or ""
        if not db_name or not ensure_loja_database_config(db_name, conn_max_age=0):
            return False
        set_current_tenant_db(db_name)
        set_current_loja_id(getattr(loja, "id", None))
        vendedor = Vendedor.objects.filter(pk=vinculo.vendedor_id).only("is_admin").first()
        return bool(vendedor and vendedor.is_admin is True)
    except Exception:
        logger.warning("backup: sem leitura do vendedor da loja %s", getattr(loja, "id", None))
        return False
    finally:
        set_current_tenant_db(anterior_db)
        set_current_loja_id(anterior_loja)


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

        # Backup da loja: dono, superadmin e suporte já passaram acima.
        # Na clínica o administrador exporta. A importação, que substitui a loja, não.
        # No CRM só o vendedor administrador exporta e importa.
        if hasattr(obj, "id"):
            from ..models import UsuarioSistema
            action = getattr(view, "action", None)
            if action in _ACOES_BACKUP_DA_LOJA or action == "importar_backup":
                if action in _ACOES_BACKUP_DA_LOJA:
                    vinculo = (
                        ProfissionalUsuario.objects.filter(user=request.user, loja=obj)
                        .only("perfil")
                        .first()
                    )
                    if vinculo and vinculo.perfil == ProfissionalUsuario.PERFIL_ADMINISTRADOR:
                        return True
                if UsuarioSistema.objects.filter(user=request.user, lojas_acesso=obj, is_active=True).exists():
                    return True
                if _vendedor_crm_e_admin(request.user, obj):
                    return True

        return False


class IsSuperAdmin(permissions.BasePermission):
    """Permissão APENAS para super admins - SEGURANÇA CRÍTICA"""

    def has_permission(self, request, view):
        return request.user and request.user.is_superuser and request.user.is_active
