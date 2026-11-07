"""Quem pode emitir, cancelar e alterar o link da NFS-e da loja.

Na clínica, só o dono e o administrador. No CRM, o vendedor emite e reenvia;
cancelar, excluir e gravar link ficam com o dono e o vendedor administrador.
"""
from __future__ import annotations

from rest_framework.permissions import BasePermission

from nfse_integration.config_loja import TIPOS_CONFIG_CLINICA, tipo_codigo_loja

ACOES_SO_ADMIN = frozenset({
    "cancelar",
    "destroy",
    "salvar_url",
    "recuperar_issnet",
    "sincronizar_asaas",
    "sincronizar_issnet",
})


def loja_da_requisicao(request):
    from superadmin.models import Loja
    from tenants.middleware import ensure_loja_context, get_current_loja_id

    ensure_loja_context(request)
    loja_id = get_current_loja_id()
    if not loja_id:
        return None
    return Loja.objects.using("default").select_related("tipo_loja").filter(id=loja_id).first()


def _e_clinica(loja) -> bool:
    return tipo_codigo_loja(loja) in TIPOS_CONFIG_CLINICA


def _vendedor_administrador(user, loja) -> bool:
    from crm_vendas.models import Vendedor
    from superadmin.models import VendedorUsuario

    vinculo = VendedorUsuario.objects.using("default").filter(user=user, loja=loja).first()
    if not vinculo or not vinculo.vendedor_id:
        return False
    try:
        vendedor = Vendedor.objects.filter(pk=vinculo.vendedor_id, loja_id=loja.id).only("is_admin").first()
    except Exception:
        return False
    return bool(vendedor and vendedor.is_admin)


def usuario_admin_nfse(user, loja) -> bool:
    from core.tenant_access import user_is_loja_admin

    if user_is_loja_admin(user, loja):
        return True
    if _e_clinica(loja):
        return False
    return _vendedor_administrador(user, loja)


def pode_acao_nfse(user, loja, acao: str) -> tuple[bool, str]:
    """Devolve (permitido, mensagem). Leitura e reenvio exigem só o vínculo com a loja."""
    if not user or not getattr(user, "is_authenticated", False):
        return False, "Autenticação necessária."
    if getattr(user, "is_superuser", False):
        return True, ""
    if loja is None:
        if acao in ("list", "retrieve", "download_pdf", "download_xml", "buscar_tomador"):
            return True, ""
        return False, "Loja não identificada."

    from core.tenant_access import user_can_access_loja

    if not user_can_access_loja(user, loja):
        return False, "Acesso permitido apenas a usuários desta loja."

    clinica = _e_clinica(loja)
    acao_de_admin = acao in ACOES_SO_ADMIN or (acao == "emitir" and clinica)
    if not acao_de_admin:
        return True, ""
    if usuario_admin_nfse(user, loja):
        return True, ""
    if clinica:
        return False, "Só o administrador da clínica pode emitir, cancelar ou alterar a nota."
    return False, "Só o administrador do CRM pode cancelar ou alterar o link da nota."


class PodeOperarNFSe(BasePermission):
    message = "Sem permissão para esta nota fiscal."

    def has_permission(self, request, view):
        acao = getattr(view, "action", "") or ""
        ok, mensagem = pode_acao_nfse(request.user, loja_da_requisicao(request), acao)
        if not ok and mensagem:
            self.message = mensagem
        return ok
