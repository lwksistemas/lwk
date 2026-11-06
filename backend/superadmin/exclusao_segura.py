"""Confirmação e trava da exclusão de loja e de usuário do sistema."""
from __future__ import annotations

import secrets


def confirmacao_confere(request, esperado: str) -> bool:
    data = getattr(request, "data", None)
    bruto = ""
    if isinstance(data, dict):
        bruto = str(data.get("confirmacao") or "")
    return secrets.compare_digest(bruto, esperado or "")


def eh_ultimo_superadmin_ativo(usuario) -> bool:
    if getattr(usuario, "tipo", "") != "superadmin" or not getattr(usuario, "is_active", False):
        return False
    from superadmin.models import UsuarioSistema

    return UsuarioSistema.objects.filter(tipo="superadmin", is_active=True).count() <= 1


def ip_do_pedido(request) -> str:
    meta = getattr(request, "META", None) or {}
    forwarded = meta.get("HTTP_X_FORWARDED_FOR", "")
    partes = [parte.strip() for parte in forwarded.split(",") if parte.strip()]
    if partes:
        return partes[-1]
    return meta.get("REMOTE_ADDR") or "127.0.0.1"


def registrar_exclusao(*, request, email: str, nome: str, recurso: str, recurso_id: int | None, detalhes: str) -> None:
    from superadmin.models import HistoricoAcessoGlobal

    ator = getattr(request, "user", None)
    HistoricoAcessoGlobal.objects.create(
        user=ator if getattr(ator, "is_authenticated", False) else None,
        usuario_email=(getattr(ator, "email", "") or email or "auditoria@lwksistemas.com.br")[:254],
        usuario_nome=(getattr(ator, "get_full_name", lambda: "")() or getattr(ator, "username", "") or nome)[:200],
        acao="excluir",
        recurso=recurso[:100],
        recurso_id=recurso_id,
        detalhes=detalhes,
        ip_address=ip_do_pedido(request),
        metodo_http="DELETE",
    )
