"""Recuperação de senha de superadmin e suporte.

O pedido só envia um link. A senha atual permanece até o link ser aberto.
A resposta é a mesma quando o e-mail não existe.
"""
from __future__ import annotations

import logging
import secrets
from html import escape
from typing import Any
from urllib.parse import quote

from django.contrib.auth.models import User
from django.core import signing
from django.core.cache import cache
from rest_framework import status as http_status

from .provisional_password_helpers import frontend_base_url, sistema_usuario_login_url

logger = logging.getLogger(__name__)

_TOKEN_SALT = "lwk-sistema-password-recovery-v1"
_TOKEN_MAX_AGE = 3600
_TIPOS = frozenset({"superadmin", "suporte"})
_OK_MESSAGE = (
    "Se o email estiver cadastrado para este acesso, você receberá um link "
    "para criar uma nova senha. A senha atual continua válida até o link ser aberto."
)

def _nonce_key(user_id: int, tipo: str) -> str:
    return f"sistema_pwd_nonce:{user_id}:{tipo}"


def _mensagem_ok() -> tuple[dict[str, Any], int]:
    return ({"message": _OK_MESSAGE}, http_status.HTTP_200_OK)


def _enviar_link(email: str, nome: str, link: str, tipo_display: str) -> None:
    from core.email_delivery import create_email_multipart, send_prepared
    from core.email_sync_context import email_sync_only

    assunto = f"Recuperação de senha - LWK Sistemas ({tipo_display})"
    texto = (
        f"Olá {nome},\n\n"
        "Recebemos um pedido para criar uma nova senha de acesso.\n"
        "A senha atual continua válida até você abrir o link abaixo. "
        "Ele expira em 1 hora e só pode ser usado uma vez.\n\n"
        f"{link}\n\n"
        "Se você não pediu esta alteração, ignore este email.\n"
    )
    html = (
        f"<p>Olá {escape(nome)},</p>"
        "<p>Recebemos um pedido para criar uma nova senha de acesso. "
        "A senha atual continua válida até você abrir o link. "
        "Ele expira em 1 hora e só pode ser usado uma vez.</p>"
        f'<p><a href="{escape(link)}">Criar nova senha</a></p>'
        "<p>Se você não pediu esta alteração, ignore este email.</p>"
    )
    email_msg = create_email_multipart(assunto, texto, [email], html=html)
    token = email_sync_only.set(True)
    try:
        send_prepared(email_msg)
    finally:
        email_sync_only.reset(token)


class SistemaPasswordRecoveryService:
    def solicitar(self, email: str, tipo: str) -> tuple[dict[str, Any], int]:
        email = (email or "").strip()
        tipo = (tipo or "").strip().lower()
        if not email or tipo not in _TIPOS:
            return (
                {"detail": "Email e tipo são obrigatórios"},
                http_status.HTTP_400_BAD_REQUEST,
            )

        from ..models import UsuarioSistema

        user = User.objects.filter(email__iexact=email).first()
        perfil = None
        if user is not None:
            perfil = UsuarioSistema.objects.filter(user=user, tipo=tipo, is_active=True).first()
        if perfil is None:
            logger.info("Recuperação de senha do sistema ignorada (tipo=%s)", tipo)
            return _mensagem_ok()

        nonce = secrets.token_urlsafe(18)
        cache.set(_nonce_key(user.id, tipo), nonce, _TOKEN_MAX_AGE)
        token = signing.dumps(
            {"uid": user.id, "tipo": tipo, "nonce": nonce},
            salt=_TOKEN_SALT,
        )
        link = (
            f"{frontend_base_url()}/{tipo}/recuperar-senha?token={quote(token, safe='')}"
        )
        tipo_display = "Super Admin" if tipo == "superadmin" else "Suporte"
        try:
            _enviar_link(
                email,
                user.first_name or user.username,
                link,
                tipo_display,
            )
        except Exception:
            logger.exception("Falha ao enviar link de recuperação (tipo=%s)", tipo)
        return _mensagem_ok()

    def confirmar(self, token: str) -> tuple[dict[str, Any], int]:
        bruto = (token or "").strip()
        if not bruto:
            return ({"detail": "Link inválido ou expirado."}, http_status.HTTP_400_BAD_REQUEST)
        try:
            data = signing.loads(bruto, salt=_TOKEN_SALT, max_age=_TOKEN_MAX_AGE)
        except (signing.BadSignature, signing.SignatureExpired, ValueError, TypeError):
            return ({"detail": "Link inválido ou expirado."}, http_status.HTTP_400_BAD_REQUEST)
        if not isinstance(data, dict):
            return ({"detail": "Link inválido ou expirado."}, http_status.HTTP_400_BAD_REQUEST)

        tipo = (data.get("tipo") or "").strip().lower()
        nonce = data.get("nonce") or ""
        try:
            user_id = int(data.get("uid"))
        except (TypeError, ValueError):
            return ({"detail": "Link inválido ou expirado."}, http_status.HTTP_400_BAD_REQUEST)
        if tipo not in _TIPOS or not nonce:
            return ({"detail": "Link inválido ou expirado."}, http_status.HTTP_400_BAD_REQUEST)

        chave = _nonce_key(user_id, tipo)
        atual = cache.get(chave)
        if not atual or not secrets.compare_digest(str(atual), str(nonce)):
            return ({"detail": "Link inválido ou expirado."}, http_status.HTTP_400_BAD_REQUEST)
        cache.delete(chave)

        from core.password_validation import generate_provisional_password

        from ..models import UsuarioSistema

        perfil = (
            UsuarioSistema.objects.select_related("user")
            .filter(user_id=user_id, tipo=tipo, is_active=True)
            .first()
        )
        if perfil is None:
            return ({"detail": "Link inválido ou expirado."}, http_status.HTTP_400_BAD_REQUEST)

        nova_senha = generate_provisional_password()
        user = perfil.user
        user.set_password(nova_senha)
        user.save(update_fields=["password"])
        perfil.senha_provisoria = nova_senha
        perfil.senha_foi_alterada = False
        perfil.save(update_fields=["senha_provisoria", "senha_foi_alterada"])

        return (
            {
                "message": "Senha provisória criada. Anote agora: ela aparece só nesta tela.",
                "senha_provisoria": nova_senha,
                "usuario": user.username,
                "url_login": sistema_usuario_login_url(tipo),
                "tipo": tipo,
            },
            http_status.HTTP_200_OK,
        )
