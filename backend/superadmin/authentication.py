"""Authenticator customizado que verifica sessão única usando banco de dados.
Garante bloqueio de acesso simultâneo: se outro dispositivo fez login,
o token antigo é invalidado imediatamente (não espera heartbeat de 60s).
"""
import contextlib
import logging
from urllib.parse import urlparse

from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication

from superadmin.session_manager import SESSION_TIMEOUT_MINUTES

logger = logging.getLogger(__name__)

# Cache em memória para evitar query no DB a cada request.
# Formato: { user_id: (session_id, timestamp) }
# Invalidado a cada 10 segundos por user.
_session_cache = {}
_CACHE_TTL_SECONDS = 10


def invalidate_session_cache(user_id: int | None = None) -> None:
    """Limpa cache de sessão (ex.: após refresh token)."""
    if user_id is None:
        _session_cache.clear()
    else:
        _session_cache.pop(user_id, None)


_METODOS_SEM_CHECAGEM_DE_ORIGEM = frozenset({"GET", "HEAD", "OPTIONS"})


def canonica_origem(valor: str) -> str:
    """scheme://host[:porta], sem caminho. Porta padrão some. null vira vazio."""
    texto = (valor or "").strip()
    if not texto or texto.lower() == "null":
        return ""
    partes = urlparse(texto)
    if partes.scheme not in {"http", "https"} or not partes.hostname:
        return ""
    host = partes.hostname.lower()
    porta = partes.port
    if porta and not (
        (partes.scheme == "https" and porta == 443) or (partes.scheme == "http" and porta == 80)
    ):
        return f"{partes.scheme}://{host}:{porta}"
    return f"{partes.scheme}://{host}"


def origem_declarada(request) -> str:
    origem = canonica_origem(request.META.get("HTTP_ORIGIN") or "")
    if origem:
        return origem
    return canonica_origem(request.META.get("HTTP_REFERER") or "")


def recusar_cookie_sem_origem(request) -> None:
    """POST (e o resto que altera) autenticado só pelo cookie precisa de origem da lista.

    Bearer explícito não entra aqui: script e mídia não mandam o cookie como prova.
    GET, HEAD e OPTIONS seguem, porque o CORS já impede o navegador de ler a resposta.
    """
    if request.method in _METODOS_SEM_CHECAGEM_DE_ORIGEM:
        return
    if request.META.get("HTTP_AUTHORIZATION"):
        return
    from core.auth_cookies import ACCESS_COOKIE

    if not request.COOKIES.get(ACCESS_COOKIE):
        return
    permitidas = {
        canonica_origem(item)
        for item in getattr(settings, "CORS_ALLOWED_ORIGINS", ())
    }
    permitidas.discard("")
    if origem_declarada(request) in permitidas:
        return
    raise PermissionDenied({
        "detail": "Origem não autorizada para esta sessão.",
        "code": "ORIGIN_NOT_ALLOWED",
    })


class SessionAwareJWTAuthentication(JWTAuthentication):
    """Authenticator JWT que verifica sessão única usando PostgreSQL.
    Garante que cada usuário tenha apenas uma sessão ativa por vez.

    Fluxo:
    0. Se o token veio só do cookie e o método altera dados, a origem tem de estar na lista
    1. Valida JWT normalmente
    2. Extrai X-Session-ID do header (enviado pelo frontend)
    3. Compara com session_id no banco (com cache de 10s)
    4. Se diferente → rejeita com DIFFERENT_SESSION (401)
    5. Se expirado por inatividade → rejeita com TIMEOUT (401)
    """

    def authenticate(self, request):
        """Autentica o usuário e verifica sessão única.
        """
        from django.db import OperationalError

        from core.auth_cookies import get_session_id_from_request, inject_bearer_from_cookie
        from core.retry import execute_with_db_retry

        recusar_cookie_sem_origem(request)
        inject_bearer_from_cookie(request)

        try:
            result = execute_with_db_retry(
                lambda: super(SessionAwareJWTAuthentication, self).authenticate(request),
                max_retries=3,
                initial_delay=1,
            )
        except OperationalError as e:
            logger.error("Falha na autenticação JWT após retries: %s", e)
            raise AuthenticationFailed({
                "detail": "Erro ao conectar ao banco de dados. Tente novamente.",
                "code": "database_timeout",
            })

        if result is None:
            return None

        user, token = result

        # Ignorar validação de sessão para endpoints de auth (login/logout/refresh)
        if request.path.startswith("/api/auth/"):
            return user, token

        client_session_id = get_session_id_from_request(request)

        if not client_session_id:
            logger.warning(
                "Sessão rejeitada: X-Session-ID ausente user_id=%s path=%s",
                user.id, request.path,
            )
            raise AuthenticationFailed({
                "detail": "Sessão inválida. Faça login novamente.",
                "code": "NO_SESSION_HEADER",
                "message": "Identificador de sessão ausente. Faça login novamente.",
            })

        # Validar sessão única com cache
        validation = self._validate_with_cache(user.id, client_session_id)

        if not validation["valid"]:
            reason = validation.get("reason", "UNKNOWN")
            message = validation.get("message", "Sessão inválida")
            logger.warning(
                "🚫 Sessão bloqueada: user_id=%s reason=%s path=%s",
                user.id, reason, request.path,
            )
            raise AuthenticationFailed({
                "detail": message,
                "code": reason,
                "message": message,
            })

        return user, token

    def _validate_with_cache(self, user_id: int, client_session_id: str, _db_retry: bool = False) -> dict:
        """Valida sessão usando cache em memória (TTL de 10s).
        Evita query no DB a cada request.
        """
        import time as _time

        from superadmin.models import UserSession

        now = _time.time()
        cached = _session_cache.get(user_id)

        # Se cache válido e o sid bate, aceita. Se diverge, consulta o DB:
        # o cache é por worker (Gunicorn) e um login novo em outro worker
        # deixa sid antigo aqui — rejeitar no cache expulsaria o aparelho que acabou de entrar.
        if cached:
            cached_sid, cached_ts = cached
            if (now - cached_ts) < _CACHE_TTL_SECONDS:
                if cached_sid == client_session_id:
                    return {"valid": True}
                _session_cache.pop(user_id, None)

        # Cache expirado ou inexistente — consultar DB
        try:
            session = UserSession.objects.filter(user_id=user_id).first()

            if not session:
                # Sem sessão no banco — sessão foi destruída (logout)
                _session_cache.pop(user_id, None)
                return {
                    "valid": False,
                    "reason": "NO_SESSION",
                    "message": "Nenhuma sessão ativa encontrada. Faça login novamente.",
                }

            # Verificar timeout de inatividade
            if session.is_expired(SESSION_TIMEOUT_MINUTES):
                session.delete()
                _session_cache.pop(user_id, None)
                return {
                    "valid": False,
                    "reason": "TIMEOUT",
                    "message": f"Sessão expirou por inatividade ({SESSION_TIMEOUT_MINUTES} minutos). Faça login novamente.",
                }

            # Atualizar cache
            _session_cache[user_id] = (session.session_id, now)

            # Comparar session_id
            if session.session_id != client_session_id:
                return {
                    "valid": False,
                    "reason": "DIFFERENT_SESSION",
                    "message": "Sessão encerrada — login realizado em outro dispositivo. Faça login novamente.",
                }

            # Sessão válida — atualizar atividade (best-effort)
            with contextlib.suppress(Exception):
                session.update_activity()

            return {"valid": True}

        except Exception as e:
            logger.error("session.validate_with_cache: error: %s", e)
            if not _db_retry:
                return self._validate_with_cache(user_id, client_session_id, _db_retry=True)
            return {
                "valid": False,
                "reason": "SESSION_DB_ERROR",
                "message": "Erro ao validar sessão. Tente novamente em instantes.",
            }
