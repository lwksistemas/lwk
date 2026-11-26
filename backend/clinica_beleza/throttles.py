"""Rate limiting para views públicas da Clínica da Beleza.

Views públicas (sem autenticação) são protegidas contra abuso via throttle
baseado em IP usando o cache do Django.

Uso em views DRF (APIView):
    throttle_classes = [PublicPdfThrottle]

Uso em views Django puras (View):
    check_rate_limit(request, "public_assinatura", "30/min")
"""
from rest_framework.throttling import AnonRateThrottle


def _get_client_ip(request) -> str:
    """IP que o proxy acrescentou no fim de X-Forwarded-For.

    O primeiro endereço da lista é enviado pelo cliente e não serve de limite.
    Sem o cabeçalho, vale o endereço da conexão.
    """
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    partes = [parte.strip() for parte in forwarded.split(",") if parte.strip()]
    if partes:
        return partes[-1]
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


class _IpDoProxyMixin:
    def get_ident(self, request):
        return _get_client_ip(request)


class PublicConfirmacaoThrottle(_IpDoProxyMixin, AnonRateThrottle):
    """30 req/min por IP — confirmação de agendamento pelo paciente."""

    scope = "public_confirmacao"
    rate = "30/min"


class PublicPdfThrottle(_IpDoProxyMixin, AnonRateThrottle):
    """30 req/min por IP — PDF público (recibo, orçamento, pedido, termo)."""

    scope = "public_pdf"
    rate = "30/min"


def check_rate_limit(request, scope: str, rate: str) -> bool:
    """Verifica rate limit baseado em cache para views Django puras (não DRF).

    Contagem atômica (add + incr) para não furar o teto sob workers concorrentes.

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

    cache.add(cache_key, 0, seconds)
    try:
        count = cache.incr(cache_key)
    except ValueError:
        cache.set(cache_key, 1, seconds)
        count = 1
    return count <= num
