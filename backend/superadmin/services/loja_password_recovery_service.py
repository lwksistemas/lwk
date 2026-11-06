"""Recuperação pública de senha do proprietário da loja (email + slug).
"""
from __future__ import annotations

import logging
from typing import Any

from django.contrib.auth.models import User
from rest_framework import status as http_status

from ..loja_utils import resolve_loja_by_slug_or_atalho
from ..models import ProfissionalUsuario, VendedorUsuario
from .provisional_password_helpers import loja_login_absolute_url

logger = logging.getLogger(__name__)

_RECOVERY_OK_MESSAGE = (
    "Se o email estiver cadastrado para esta loja, você receberá um link "
    "para criar uma nova senha. A senha atual continua válida até o link ser aberto."
)
_TOKEN_SALT = "lwk-loja-password-recovery-v1"
_TOKEN_MAX_AGE = 3600

_REQUEST_LIMIT_PER_IP = 30
_REQUEST_WINDOW_SECONDS = 3600
_SEND_LIMIT_PER_EMAIL = 3
_SEND_LIMIT_PER_IP = 5
_SEND_WINDOW_SECONDS = 3600


def _client_ip(request) -> str:
    """Último endereço de X-Forwarded-For, o que o proxy acrescenta.

    O primeiro valor é enviado pelo cliente e não serve de limite.
    """
    if request is None:
        return "0.0.0.0"
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    partes = [parte.strip() for parte in forwarded.split(",") if parte.strip()]
    if partes:
        return partes[-1]
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


def _nonce_key(user_id: int, loja_id: int) -> str:
    return f"loja_pwd_nonce:{user_id}:{loja_id}"


def _retry_after_seconds(cache_key: str, window_seconds: int) -> int:
    from django.core.cache import cache

    if hasattr(cache, "ttl"):
        ttl = cache.ttl(cache_key)
        if ttl is not None and ttl > 0:
            return int(ttl)
    return window_seconds


def _rate_limit_response(retry_after: int) -> tuple[dict[str, Any], int]:
    minutes = max(1, (retry_after + 59) // 60)
    return (
        {
            "detail": (
                f"Muitas solicitações de recuperação de senha. "
                f"Tente novamente em cerca de {minutes} minuto(s)."
            ),
            "retry_after": retry_after,
        },
        http_status.HTTP_429_TOO_MANY_REQUESTS,
    )


def check_loja_password_recovery_request_limit(request) -> tuple[dict[str, Any], int] | None:
    """Limite leve por IP para evitar abuso do endpoint (não bloqueia testes normais)."""
    if request is None:
        return None
    from django.core.cache import cache

    ip = _client_ip(request)
    cache_key = f"pwd_recovery_req:{ip}"
    count = cache.get(cache_key, 0)
    if count >= _REQUEST_LIMIT_PER_IP:
        return _rate_limit_response(_retry_after_seconds(cache_key, _REQUEST_WINDOW_SECONDS))
    if count == 0:
        cache.set(cache_key, 1, _REQUEST_WINDOW_SECONDS)
    else:
        ttl = cache.ttl(cache_key) if hasattr(cache, "ttl") else _REQUEST_WINDOW_SECONDS
        cache.set(cache_key, count + 1, ttl or _REQUEST_WINDOW_SECONDS)
    return None


def check_loja_password_recovery_send_limit(
    request,
    email: str,
    slug: str,
) -> tuple[dict[str, Any], int] | None:
    """Limite apenas quando um email de recuperação será enviado de fato."""
    if request is None:
        return None
    from django.core.cache import cache

    ip = _client_ip(request)
    email_norm = (email or "").strip().lower()
    slug_norm = (slug or "").strip().lower()
    keys = [
        (f"pwd_recovery_send:ip:{ip}", _SEND_LIMIT_PER_IP),
        (f"pwd_recovery_send:{slug_norm}:{email_norm}", _SEND_LIMIT_PER_EMAIL),
    ]
    for cache_key, limit in keys:
        if cache.get(cache_key, 0) >= limit:
            return _rate_limit_response(
                _retry_after_seconds(cache_key, _SEND_WINDOW_SECONDS),
            )
    for cache_key, _limit in keys:
        count = cache.get(cache_key, 0)
        if count == 0:
            cache.set(cache_key, 1, _SEND_WINDOW_SECONDS)
        else:
            ttl = cache.ttl(cache_key) if hasattr(cache, "ttl") else _SEND_WINDOW_SECONDS
            cache.set(cache_key, count + 1, ttl or _SEND_WINDOW_SECONDS)
    return None


def resolve_loja_user_for_password_recovery(loja, email: str) -> User | None:
    """Usuário com acesso à loja cujo email coincide (proprietário, profissional ou vendedor).
    Busca também o email no cadastro do tenant (Professional/Vendedor), pois pode divergir do User.email.
    """
    email_norm = (email or "").strip().lower()
    if not email_norm or not loja:
        return None

    owner = loja.owner
    if owner and (owner.email or "").strip().lower() == email_norm:
        return owner

    user = User.objects.filter(email__iexact=email.strip()).first()
    if user:
        if ProfissionalUsuario.objects.filter(user=user, loja=loja).exists():
            return user
        if VendedorUsuario.objects.filter(user=user, loja=loja).exists():
            return user

    return _resolve_user_by_tenant_email(loja, email_norm)


def _resolve_user_by_tenant_email(loja, email_norm: str) -> User | None:
    """Resolve User via email cadastrado no profissional/vendedor do schema da loja."""
    db = getattr(loja, "database_name", None)
    if not db or not getattr(loja, "database_created", False):
        return None

    from core.db_config import ensure_loja_database_config

    if not ensure_loja_database_config(db, conn_max_age=60):
        return None

    tipo_slug = (getattr(loja.tipo_loja, "slug", None) or "").strip().lower()
    tipo_nome = (getattr(loja.tipo_loja, "nome", None) or "").strip()

    prof_id = _find_tenant_professional_id(loja, db, email_norm, tipo_slug, tipo_nome)
    if prof_id is not None:
        pu = (
            ProfissionalUsuario.objects.filter(loja=loja, professional_id=prof_id)
            .select_related("user")
            .first()
        )
        if pu and pu.user_id:
            return pu.user

    vendedor_id = _find_tenant_vendedor_id(loja, db, email_norm, tipo_slug, tipo_nome)
    if vendedor_id is not None:
        vu = (
            VendedorUsuario.objects.filter(loja=loja, vendedor_id=vendedor_id)
            .select_related("user")
            .first()
        )
        if vu and vu.user_id:
            return vu.user

    return None


def _find_tenant_professional_id(loja, db: str, email_norm: str, tipo_slug: str, tipo_nome: str):
    prof_model = None
    if tipo_slug == "clinica-beleza" or tipo_nome == "Clínica da Beleza":
        from clinica_beleza.models import Professional as prof_model

    if prof_model is None:
        return None

    try:
        prof = (
            prof_model.objects.using(db)
            .filter(loja_id=loja.id, email__iexact=email_norm, is_active=True)
            .values_list("id", flat=True)
            .first()
        )
        return prof
    except Exception as exc:
        logger.debug("Recuperação de senha: busca profissional tenant falhou (loja=%s): %s", loja.slug, exc)
        return None


def _find_tenant_vendedor_id(loja, db: str, email_norm: str, tipo_slug: str, tipo_nome: str):
    if tipo_slug != "crm-vendas" and tipo_nome != "CRM Vendas":
        return None
    try:
        from crm_vendas.models import Vendedor

        return (
            Vendedor.objects.using(db)
            .filter(loja_id=loja.id, email__iexact=email_norm, is_active=True)
            .values_list("id", flat=True)
            .first()
        )
    except Exception as exc:
        logger.debug("Recuperação de senha: busca vendedor tenant falhou (loja=%s): %s", loja.slug, exc)
        return None


class LojaPasswordRecoveryService:
    """Encapsula validação, geração de senha e envio de email."""

    def execute(self, email: str, slug: str, request=None) -> tuple[dict[str, Any], int]:
        if not email or not slug:
            return (
                {"detail": "Email e slug são obrigatórios"},
                http_status.HTTP_400_BAD_REQUEST,
            )

        limited = check_loja_password_recovery_request_limit(request)
        if limited:
            return limited

        loja = resolve_loja_by_slug_or_atalho(
            slug,
            is_active=True,
            select_related=("owner", "tipo_loja", "plano"),
        )
        user = resolve_loja_user_for_password_recovery(loja, email) if loja else None
        if not user:
            logger.info(
                "Recuperação de senha loja: solicitação ignorada (identificador=%s, loja_encontrada=%s)",
                slug,
                bool(loja),
            )
            return ({"message": _RECOVERY_OK_MESSAGE}, http_status.HTTP_200_OK)

        limited = check_loja_password_recovery_send_limit(request, email, slug)
        if limited:
            return limited

        import secrets
        from html import escape
        from urllib.parse import quote

        from django.core import signing
        from django.core.cache import cache

        from .provisional_password_helpers import frontend_base_url

        nonce = secrets.token_urlsafe(18)
        cache.set(_nonce_key(user.id, loja.id), nonce, _TOKEN_MAX_AGE)
        token = signing.dumps(
            {"uid": user.id, "loja": loja.id, "nonce": nonce},
            salt=_TOKEN_SALT,
        )
        atalho = (getattr(loja, "atalho", "") or "").strip() or loja.slug
        link = (
            f"{frontend_base_url()}/loja/{quote(atalho, safe='')}/recuperar-senha"
            f"?token={quote(token, safe='')}"
        )
        nome = user.first_name or user.username
        assunto = f"Recuperação de senha - {loja.nome}"
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
        try:
            from core.email_delivery import create_email_multipart, send_prepared
            from core.email_sync_context import email_sync_only

            email_msg = create_email_multipart(assunto, texto, [email.strip()], html=html)
            sync = email_sync_only.set(True)
            try:
                send_prepared(email_msg, fail_silently=False)
            finally:
                email_sync_only.reset(sync)
        except Exception as e:
            logger.exception("Erro ao enviar email de recuperação de senha: %s", e)
            return (
                {"detail": "Erro ao enviar email de recuperação. Tente novamente mais tarde."},
                http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return ({"message": _RECOVERY_OK_MESSAGE}, http_status.HTTP_200_OK)

    def confirmar(self, token: str) -> tuple[dict[str, Any], int]:
        """Troca a senha só quando o link é aberto. A senha aparece uma vez e não fica gravada."""
        import secrets

        from django.core import signing
        from django.core.cache import cache

        bruto = (token or "").strip()
        if not bruto:
            return ({"detail": "Link inválido ou expirado."}, http_status.HTTP_400_BAD_REQUEST)
        try:
            data = signing.loads(bruto, salt=_TOKEN_SALT, max_age=_TOKEN_MAX_AGE)
        except (signing.BadSignature, signing.SignatureExpired, ValueError, TypeError):
            return ({"detail": "Link inválido ou expirado."}, http_status.HTTP_400_BAD_REQUEST)
        if not isinstance(data, dict):
            return ({"detail": "Link inválido ou expirado."}, http_status.HTTP_400_BAD_REQUEST)
        try:
            user_id = int(data.get("uid"))
            loja_id = int(data.get("loja"))
        except (TypeError, ValueError):
            return ({"detail": "Link inválido ou expirado."}, http_status.HTTP_400_BAD_REQUEST)
        nonce = data.get("nonce") or ""
        if not nonce:
            return ({"detail": "Link inválido ou expirado."}, http_status.HTTP_400_BAD_REQUEST)

        chave = _nonce_key(user_id, loja_id)
        atual = cache.get(chave)
        if not atual or not secrets.compare_digest(str(atual), str(nonce)):
            return ({"detail": "Link inválido ou expirado."}, http_status.HTTP_400_BAD_REQUEST)
        cache.delete(chave)

        from django.contrib.auth.models import User

        from core.password_validation import generate_provisional_password

        from ..models import Loja

        loja = (
            Loja.objects.select_related("owner")
            .filter(id=loja_id, is_active=True)
            .first()
        )
        user = User.objects.filter(id=user_id, is_active=True).first()
        if loja is None or user is None:
            return ({"detail": "Link inválido ou expirado."}, http_status.HTTP_400_BAD_REQUEST)
        vinculado = (
            loja.owner_id == user.id
            or ProfissionalUsuario.objects.filter(user=user, loja=loja).exists()
            or VendedorUsuario.objects.filter(user=user, loja=loja).exists()
        )
        if not vinculado:
            return ({"detail": "Link inválido ou expirado."}, http_status.HTTP_400_BAD_REQUEST)

        nova_senha = generate_provisional_password()
        user.set_password(nova_senha)
        user.save(update_fields=["password"])
        if loja.owner_id == user.id:
            loja.senha_provisoria = ""
            loja.senha_foi_alterada = False
            loja.save(update_fields=["senha_provisoria", "senha_foi_alterada"])
        ProfissionalUsuario.objects.filter(user=user, loja=loja).update(precisa_trocar_senha=True)
        VendedorUsuario.objects.filter(user=user, loja=loja).update(precisa_trocar_senha=True)
        return (
            {
                "message": "Senha provisória criada. Anote agora: ela aparece só nesta tela.",
                "senha_provisoria": nova_senha,
                "usuario": user.username,
                "url_login": loja_login_absolute_url(loja),
            },
            http_status.HTTP_200_OK,
        )
