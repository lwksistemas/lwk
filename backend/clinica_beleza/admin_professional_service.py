"""Service layer — owner habilita/desabilita-se como profissional na agenda."""

from __future__ import annotations

import logging

from django.contrib.auth import get_user_model

from .models import Professional

logger = logging.getLogger(__name__)
User = get_user_model()


def sincronizar_profissional_admin_owner(loja, owner=None) -> bool:
    """Alinha nome, e-mail e telefone do profissional ao administrador da loja.

    A edição no superadmin não abre o schema da clínica. Sem isso o
    profissional da agenda fica com o e-mail antigo.
    """
    from core.db_config import ensure_loja_database_config
    from superadmin.models import ProfissionalUsuario

    if owner is None:
        owner = getattr(loja, "owner", None)
    if not owner or not getattr(loja, "database_name", None) or not loja.database_created:
        return False
    if not ensure_loja_database_config(loja.database_name):
        return False

    vinculo = ProfissionalUsuario.objects.using("default").filter(user=owner, loja_id=loja.id).first()
    if not vinculo:
        return False

    nome = (owner.get_full_name() or owner.username or (owner.email or "").split("@")[0]).strip()
    if not nome:
        return False

    campos = {
        "nome": nome,
        "email": (owner.email or "").strip(),
    }
    telefone = (getattr(loja, "owner_telefone", "") or "").strip()
    if telefone:
        campos["telefone"] = telefone

    atualizados = Professional.objects.all_without_filter().using(loja.database_name).filter(
        pk=vinculo.professional_id,
        loja_id=loja.id,
    ).update(**campos)
    return atualizados > 0


def _email_owner(user) -> str:
    return (getattr(user, "email", None) or "").strip()


def _profissional_do_owner(loja_id: int, user):
    email = _email_owner(user)
    if not email:
        return None
    return Professional.objects.filter(loja_id=loja_id, email__iexact=email).first()


def obter_status_admin_profissional(loja_id: int, user) -> dict:
    """Retorna { is_enabled: bool, professional_id: int | None }.
    Habilitado = Professional ativo com is_profissional=True para o e-mail do owner.
    """
    prof = _profissional_do_owner(loja_id, user)
    if not prof:
        return {"is_enabled": False, "professional_id": None}
    enabled = bool(prof.is_active) and (prof.is_profissional is not False)
    return {"is_enabled": enabled, "professional_id": prof.id}


def habilitar_admin_como_profissional(loja_id: int, user) -> Professional:
    """Cria ou reativa Professional do owner (idempotente)."""
    from superadmin.models import Loja

    loja = Loja.objects.using("default").filter(id=loja_id).first()
    if not loja:
        raise ValueError("Loja não encontrada")

    email = _email_owner(user) or (loja.owner.email or "").strip()
    if not email:
        raise ValueError("E-mail do administrador não cadastrado.")

    nome = (user.get_full_name() or user.username or loja.owner.username or "Administrador").strip()
    telefone = getattr(loja, "owner_telefone", "") or ""

    prof = _profissional_do_owner(loja_id, user)
    if prof:
        changed = False
        if not prof.is_active:
            prof.is_active = True
            changed = True
        if prof.is_profissional is False:
            prof.is_profissional = True
            changed = True
        if not (prof.nome or "").strip():
            prof.nome = nome
            changed = True
        if changed:
            prof.save()
        return prof

    return Professional.objects.create(
        loja_id=loja_id,
        nome=nome,
        email=email,
        telefone=telefone,
        especialidade="Administrador",
        is_active=True,
        is_profissional=True,
    )


def desabilitar_admin_como_profissional(loja_id: int, user) -> None:
    """Soft-delete: is_active=False (preserva histórico). Idempotente."""
    prof = _profissional_do_owner(loja_id, user)
    if not prof or not prof.is_active:
        return
    prof.is_active = False
    prof.save(update_fields=["is_active", "updated_at"])
