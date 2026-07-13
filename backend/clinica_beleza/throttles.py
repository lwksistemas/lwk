"""Rate limiting para views públicas da Clínica da Beleza.

Views públicas (sem autenticação) são protegidas contra abuso via throttle
baseado em IP usando o cache do Django.

Uso em views DRF (APIView):
    throttle_classes = [PublicConfirmacaoThrottle]

Uso em views Django puras (View):
    Usar o decorator @throttle_public ou o mixin PublicViewThrottleMixin.
"""
from rest_framework.throttling import AnonRateThrottle


class PublicConfirmacaoThrottle(AnonRateThrottle):
    """30 req/min por IP — confirmação de agendamento pelo paciente."""

    scope = "public_confirmacao"
    rate = "30/min"


class PublicAssinaturaThrottle(AnonRateThrottle):
    """30 req/min por IP — assinatura de termo de consentimento."""

    scope = "public_assinatura"
    rate = "30/min"


class PublicFotoThrottle(AnonRateThrottle):
    """10 req/min por IP — envio de foto pelo paciente via QR."""

    scope = "public_foto"
    rate = "10/min"


def _get_client_ip(request) -> str:
    """Extrai IP real do request respeitando proxies."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


def check_rate_limit(request, scope: str, rate: str) -> bool:
    """Verifica rate limit baseado em cache para views Django puras (não DRF).

    Args:
        request: HttpRequest
        scope: identificador do throttle (ex: 'public_foto')
        rate: taxa no formato 'N/unit' (ex: '10/min', '30/min')

    Returns:
        True se a requisição está dentro do limite, False se excedeu.

    """
    from django.core.cache import cache

    try:
        num, period = rate.split("/")
        num = int(num)
        seconds = {"min": 60, "hour": 3600, "day": 86400}.get(period, 60)
    except (ValueError, KeyError):
        return True  # falha segura: permite requisição

    ip = _get_client_ip(request)
    cache_key = f"throttle_{scope}_{ip}"

    count = cache.get(cache_key, 0)
    if count >= num:
        return False

    # Incrementa contador; set com timeout só na primeira vez para preservar janela
    if count == 0:
        cache.set(cache_key, 1, seconds)
    else:
        cache.set(cache_key, count + 1, cache.ttl(cache_key) if hasattr(cache, "ttl") else seconds)

    return True
