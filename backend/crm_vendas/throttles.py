"""Limite das rotas públicas do CRM pelo IP que o proxy acrescentou."""
from django.core.cache import cache
from rest_framework.throttling import AnonRateThrottle


def ip_do_proxy(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    partes = [parte.strip() for parte in forwarded.split(",") if parte.strip()]
    if partes:
        return partes[-1]
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


class _IpDoProxyMixin:
    def get_ident(self, request):
        return ip_do_proxy(request)


class PublicComissaoThrottle(_IpDoProxyMixin, AnonRateThrottle):
    """30 req/min por IP — link público do relatório de comissão."""

    scope = "public_comissao"
    rate = "30/min"


class PublicAssinaturaCrmThrottle(_IpDoProxyMixin, AnonRateThrottle):
    """30 req/min por IP — assinatura e PDF público do CRM."""

    scope = "public_assinatura_crm"
    rate = "30/min"


def estourou_limite_publico(request, scope: str = "public_assinatura_crm", rate: str = "30/min") -> bool:
    """True quando a view Django pura passou do limite."""
    try:
        num, period = rate.split("/")
        num = int(num)
        seconds = {"min": 60, "hour": 3600, "day": 86400}.get(period, 60)
    except (ValueError, KeyError):
        return False
    chave = f"throttle:{scope}:{ip_do_proxy(request)}"
    atual = cache.get(chave, 0)
    if atual >= num:
        return True
    if atual == 0:
        cache.set(chave, 1, seconds)
    else:
        try:
            cache.incr(chave)
        except ValueError:
            cache.set(chave, atual + 1, seconds)
    return False
