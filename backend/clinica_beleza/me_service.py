"""Contexto do usuário logado na Clínica da Beleza (nome no topo)."""

from __future__ import annotations


def resolve_user_display_name(user, *, professional_nome: str | None = None) -> str:
    """Nome para o cabeçalho: profissional vinculado, senão nome completo, senão login."""
    nome = (professional_nome or "").strip()
    if nome:
        return nome
    full = (user.get_full_name() or "").strip()
    if full:
        return full
    return (getattr(user, "username", None) or "").strip() or "Usuário"


def build_me_payload(user, loja_id: int | None) -> dict:
    """Monta GET /clinica-beleza/me/."""
    professional_id = None
    professional_nome = None
    if loja_id:
        from superadmin.models import ProfissionalUsuario

        from .models import Professional

        pu = ProfissionalUsuario.objects.filter(user=user, loja_id=loja_id).first()
        if pu and pu.professional_id:
            professional_id = pu.professional_id
            try:
                professional_nome = (
                    Professional.objects.filter(id=pu.professional_id)
                    .values_list("nome", flat=True)
                    .first()
                )
            except Exception:
                professional_nome = None

    return {
        "user_display_name": resolve_user_display_name(user, professional_nome=professional_nome),
        "username": getattr(user, "username", "") or "",
        "professional_id": professional_id,
    }
