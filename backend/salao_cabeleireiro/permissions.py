"""Acesso do salão: quem é da loja entra; só o administrador troca o painel."""
from rest_framework.permissions import BasePermission

from superadmin.models import Loja, ProfissionalUsuario


SLUGS_SALAO = (
    "salao-cabeleireiro",
    "salao-de-cabeleireiro",
    "salao-de-cabelereiro",
    "cabeleireiro",
    "cabelereiro",
)


def loja_e_salao(loja) -> bool:
    tipo = getattr(loja, "tipo_loja", None)
    slug = ((getattr(tipo, "slug", None) or "")).strip().lower()
    if slug in SLUGS_SALAO:
        return True
    nome = (getattr(tipo, "nome", None) or "").lower()
    if "clinica" in nome:
        return False
    return "cabeleireiro" in nome or "cabelereiro" in nome or "salão" in nome or "salao" in nome


def contexto_salao(request):
    cache = "_salao_loja_ctx"
    if hasattr(request, cache):
        return getattr(request, cache)
    if not request.user or not request.user.is_authenticated:
        resultado = (None, None)
        setattr(request, cache, resultado)
        return resultado
    from clinica_beleza.views_base import resolve_loja_id_from_request

    loja_id = resolve_loja_id_from_request(request)
    if not loja_id:
        resultado = (None, None)
        setattr(request, cache, resultado)
        return resultado
    loja = Loja.objects.select_related("tipo_loja").filter(pk=loja_id).first()
    if loja is None or not loja_e_salao(loja):
        resultado = (None, None)
        setattr(request, cache, resultado)
        return resultado
    if request.user.is_superuser or loja.owner_id == request.user.id:
        resultado = (loja, None)
        setattr(request, cache, resultado)
        return resultado
    prof = ProfissionalUsuario.objects.filter(user=request.user, loja=loja).first()
    resultado = (loja, prof) if prof else (None, None)
    setattr(request, cache, resultado)
    return resultado


def usuario_e_admin(loja, prof, user) -> bool:
    if user.is_superuser or loja.owner_id == user.id:
        return True
    return bool(prof) and prof.perfil == ProfissionalUsuario.PERFIL_ADMINISTRADOR


def eh_recepcao(loja, prof, user) -> bool:
    if usuario_e_admin(loja, prof, user):
        return False
    return bool(prof) and prof.perfil in {
        ProfissionalUsuario.PERFIL_RECEPCIONISTA,
        ProfissionalUsuario.PERFIL_RECEPCAO,
        ProfissionalUsuario.PERFIL_CAIXA,
    }


def papel_salao(loja, prof, user, modelo: str) -> str:
    if usuario_e_admin(loja, prof, user):
        return "autonomo" if modelo == "autonomo" else "administrador"
    if eh_recepcao(loja, prof, user):
        return "recepcionista"
    return "profissional"


class IsSalaoMembro(BasePermission):
    message = "Acesso permitido apenas a usuários deste salão."

    def has_permission(self, request, view):
        loja, prof = contexto_salao(request)
        if loja is None or not (prof is not None or loja.owner_id == request.user.id or request.user.is_superuser):
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        liberadas = {"ReceberAgendamentoView", "VendaCreateView", "SessaoAbrirView", "SessaoFecharView", "SessaoMovimentoView"}
        if eh_recepcao(loja, prof, request.user) and view.__class__.__name__ not in liberadas:
            self.message = "A recepção usa somente o Caixa/PDV."
            return False
        return True


class IsSalaoAdmin(BasePermission):
    message = "Só o administrador troca o painel deste salão."

    def has_permission(self, request, view):
        loja, prof = contexto_salao(request)
        if loja is None:
            return False
        return usuario_e_admin(loja, prof, request.user)
