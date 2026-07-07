"""
Utility de retry para operações de banco de dados com backoff exponencial.

Substitui retry logic duplicada em:
- config/security_middleware.py (SecurityIsolationMiddleware._authenticate_jwt)
- superadmin/authentication.py (SessionAwareJWTAuthentication.authenticate)
- superadmin/auth_views_secure.py (authenticate_with_retry)

Uso:
    from core.retry import retry_on_db_timeout

    @retry_on_db_timeout(max_retries=3, initial_delay=0.5)
    def minha_funcao():
        ...

    # Ou inline:
    result = retry_on_db_timeout()(lambda: connection.execute(query))()
"""
import functools
import logging
import time

from django.db import OperationalError

logger = logging.getLogger(__name__)


def retry_on_db_timeout(max_retries: int = 3, initial_delay: float = 0.5, backoff_factor: float = 2.0):
    """
    Decorator que retenta operação em caso de timeout do banco de dados.

    Args:
        max_retries: Número máximo de tentativas (padrão: 3)
        initial_delay: Delay inicial em segundos (padrão: 0.5s)
        backoff_factor: Multiplicador do delay a cada retry (padrão: 2.0x)

    Returns:
        Decorator que envolve a função com retry logic.

    Raises:
        OperationalError: Se todas as tentativas falharem.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    last_exception = e
                    if 'timeout' not in str(e).lower() or attempt >= max_retries - 1:
                        raise
                    logger.warning(
                        "DB timeout na tentativa %d/%d de %s. Retrying em %.1fs...",
                        attempt + 1, max_retries, func.__qualname__, delay,
                    )
                    time.sleep(delay)
                    delay *= backoff_factor

            raise last_exception  # pragma: no cover

        return wrapper
    return decorator


def execute_with_db_retry(callable_fn, max_retries: int = 3, initial_delay: float = 0.5):
    """
    Executa um callable com retry em caso de timeout do DB.
    Versão funcional (sem decorator) para uso inline.

    Args:
        callable_fn: Função a ser executada
        max_retries: Tentativas máximas
        initial_delay: Delay inicial

    Returns:
        Resultado do callable

    Raises:
        OperationalError: Se todas as tentativas falharem.
    """
    return retry_on_db_timeout(max_retries=max_retries, initial_delay=initial_delay)(callable_fn)()
