"""
Rate limiting para endpoints sensíveis.

Usa cache do Django (Redis em produção) para controlar requisições.
Limita por usuário + endpoint.

Uso:
    from core.rate_limit import rate_limit

    @api_view(['POST'])
    @rate_limit(max_requests=5, window_seconds=60)
    def emitir_nfse_manual(request):
        ...
"""
import contextlib
import functools
import hashlib
import logging

from django.core.cache import cache
from rest_framework.response import Response

logger = logging.getLogger(__name__)

# Prefixo para chaves no cache
RATE_LIMIT_PREFIX = 'rl:'


def rate_limit(max_requests: int = 10, window_seconds: int = 60):
    """
    Decorator de rate limiting para views DRF.

    Args:
        max_requests: Número máximo de requisições permitidas na janela
        window_seconds: Tamanho da janela em segundos
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Identificar o usuário/IP
            if request.user.is_authenticated:
                identifier = f'user:{request.user.id}'
            else:
                ip = _get_client_ip(request)
                identifier = f'ip:{ip}'

            # Chave única: prefixo + endpoint + identificador
            endpoint = f'{request.method}:{request.path}'
            key = RATE_LIMIT_PREFIX + hashlib.md5(
                f'{endpoint}:{identifier}'.encode(),
                usedforsecurity=False,
            ).hexdigest()

            # Verificar e incrementar contador
            current = cache.get(key, 0)
            if current >= max_requests:
                logger.warning(
                    'Rate limit excedido: %s em %s (%d/%d)',
                    identifier, endpoint, current, max_requests
                )
                return Response(
                    {
                        'error': 'Limite de requisições excedido. Tente novamente em alguns segundos.',
                        'retry_after': window_seconds,
                    },
                    status=429,
                )

            # Incrementar contador
            with contextlib.suppress(Exception):  # Se cache falhar, não bloquear a requisição
                cache.set(key, current + 1, timeout=window_seconds)

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def _get_client_ip(request):
    """Obtém IP real do cliente."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')
