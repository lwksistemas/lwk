"""Serviços do app suporte - lógica de negócio reutilizável.

Princípios: Single Responsibility, DRY, separação de concerns.
"""
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from .models import Chamado


def _perfil_suporte(user: User):
    if user.is_superuser:
        return None
    if not user.groups.filter(name="suporte").exists():
        return None
    try:
        from superadmin.models import UsuarioSistema

        return UsuarioSistema.objects.prefetch_related("lojas_acesso").get(
            user=user,
            tipo="suporte",
            is_active=True,
        )
    except ObjectDoesNotExist:
        return None


def suporte_pode_loja(user: User, loja) -> bool:
    if user.is_superuser:
        return True
    perfil = _perfil_suporte(user)
    if perfil is None:
        return False
    if perfil.pode_acessar_todas_lojas:
        return True
    return perfil.lojas_acesso.filter(pk=loja.pk).exists()


def _chaves_da_loja(loja) -> list[str]:
    chaves = [loja.slug]
    atalho = (getattr(loja, "atalho", None) or "").strip()
    if atalho and atalho not in chaves:
        chaves.append(atalho)
    return chaves


def _chamados_das_lojas_do_usuario(user: User):
    """Chamados abertos por este usuário, só nas lojas em que ele entra."""
    from superadmin.models import Loja, ProfissionalUsuario, VendedorUsuario

    lojas = list(Loja.objects.filter(owner=user, is_active=True))
    lojas.extend(
        pu.loja
        for pu in ProfissionalUsuario.objects.filter(user=user, loja__is_active=True).select_related("loja")
    )
    lojas.extend(
        vu.loja
        for vu in VendedorUsuario.objects.filter(user=user, loja__is_active=True).select_related("loja")
    )
    chaves: set[str] = set()
    for loja in lojas:
        chaves.update(_chaves_da_loja(loja))
    if not chaves:
        return Chamado.objects.none()
    email = (user.email or "").strip()
    if not email:
        return Chamado.objects.none()
    return Chamado.objects.filter(loja_slug__in=chaves, usuario_email__iexact=email)


def get_chamados_queryset_for_user(user: User, loja_slug: str | None = None):
    """Retorna os chamados visíveis para o usuário.

    Sem loja, o suporte global continua vendo a fila inteira (painel de suporte).
    Com loja, a resposta fica só naquela loja. A tela da loja sempre envia o slug.
    """
    if user.is_superuser:
        qs = Chamado.objects.all()
    else:
        perfil = _perfil_suporte(user)
        if perfil is not None:
            if perfil.pode_acessar_todas_lojas:
                qs = Chamado.objects.all()
            else:
                slugs = list(perfil.lojas_acesso.values_list("slug", flat=True))
                atalhos = [a for a in perfil.lojas_acesso.values_list("atalho", flat=True) if a]
                chaves = [s for s in slugs + atalhos if s]
                qs = Chamado.objects.filter(loja_slug__in=chaves) if chaves else Chamado.objects.none()
        else:
            qs = _chamados_das_lojas_do_usuario(user)

    identificador = (loja_slug or "").strip()
    if not identificador:
        return qs

    from core.tenant_access import user_can_access_loja
    from superadmin.loja_utils import resolve_loja_by_slug_or_atalho

    loja = resolve_loja_by_slug_or_atalho(identificador, is_active=True)
    if not loja:
        return Chamado.objects.none()
    if not (suporte_pode_loja(user, loja) or user_can_access_loja(user, loja)):
        return Chamado.objects.none()
    return qs.filter(loja_slug__in=_chaves_da_loja(loja))


def loja_para_novo_chamado(user: User, identificador: str):
    """Loja em que o chamado será gravado. Não usa a primeira loja do usuário."""
    from core.tenant_access import user_can_access_loja
    from superadmin.loja_utils import resolve_loja_by_slug_or_atalho
    from superadmin.models import Loja

    ident = (identificador or "").strip()
    if ident:
        loja = resolve_loja_by_slug_or_atalho(ident, is_active=True)
        if not loja:
            return None
        if suporte_pode_loja(user, loja) or user_can_access_loja(user, loja):
            return loja
        return None

    proprias = list(Loja.objects.filter(owner=user, is_active=True)[:2])
    if len(proprias) == 1:
        return proprias[0]
    return None
