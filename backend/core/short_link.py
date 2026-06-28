"""
Encurtador de URL interno — LWK Sistemas.

Gera códigos curtos (8 chars) para tokens longos de assinatura/confirmação.
Sem dependência de serviços externos. Sem risco de ban por URL estranha.

Exemplo:
    https://api.lwksistemas.com.br/r/aB3xK9mQ
    em vez de:
    https://lwksistemas.com.br/assinar/eyJkb2N...longa...

O endpoint /r/<code>/ redireciona para a URL completa.
Os links expiram automaticamente junto com o token original.
"""
import secrets
import string
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from core.models import ShortLink

ALPHABET = string.ascii_letters + string.digits  # 62 chars → 62^8 ≈ 218 trilhões de combinações
CODE_LENGTH = 8
SHORT_LINK_TTL_DAYS = 30  # links ficam no banco por 30 dias


def _generate_code() -> str:
    """Gera código único de 8 caracteres."""
    for _ in range(10):
        code = ''.join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))
        if not ShortLink.objects.using('default').filter(code=code).exists():
            return code
    # Fallback: 12 chars se colisão (extremamente raro)
    return ''.join(secrets.choice(ALPHABET) for _ in range(12))


def create_short_link(full_url: str, ttl_days: int = SHORT_LINK_TTL_DAYS) -> str:
    """
    Cria ou reutiliza um link curto para a URL completa.
    Retorna o código curto (ex.: 'aB3xK9mQ').

    Se a mesma URL já tem um link válido, reutiliza (idempotente).
    Tabela core_short_links fica SEMPRE no schema public (using='default').
    """
    from django.db.models import Q

    # Reutilizar link existente não expirado
    existing = (
        ShortLink.objects.using('default')
        .filter(full_url=full_url)
        .filter(
            Q(expires_at__isnull=True) |
            Q(expires_at__gt=timezone.now())
        )
        .order_by('-created_at')
        .first()
    )
    if existing:
        return existing.code

    code = _generate_code()
    ShortLink.objects.using('default').create(
        code=code,
        full_url=full_url,
        expires_at=timezone.now() + timedelta(days=ttl_days),
    )
    return code


def resolve_short_link(code: str) -> str | None:
    """
    Resolve código curto → URL completa.
    Retorna None se não encontrado ou expirado.
    """
    try:
        link = ShortLink.objects.using('default').get(code=code)
    except ShortLink.DoesNotExist:
        return None
    if link.is_expired:
        return None
    return link.full_url


def build_short_url(full_url: str, ttl_days: int = SHORT_LINK_TTL_DAYS) -> str:
    """
    Cria link curto e retorna a URL completa curta.
    Ex.: https://api.lwksistemas.com.br/r/aB3xK9mQ
    O endpoint /r/<code>/ no backend redireciona para a URL completa.
    """
    try:
        code = create_short_link(full_url, ttl_days=ttl_days)
        base = (
            getattr(settings, 'API_BASE_URL', None)
            or getattr(settings, 'BACKEND_URL', None)
            or getattr(settings, 'FRONTEND_URL', 'https://lwksistemas.com.br')
        ).rstrip('/')
        return f'{base}/r/{code}'
    except Exception:
        # Fallback seguro: retornar URL original se o banco falhar
        return full_url
