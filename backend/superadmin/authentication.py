"""
Authenticator customizado que verifica sessão única usando banco de dados.
Garante bloqueio de acesso simultâneo: se outro dispositivo fez login,
o token antigo é invalidado imediatamente (não espera heartbeat de 60s).
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from superadmin.session_manager import SessionManager, SESSION_TIMEOUT_MINUTES
import logging
import time

logger = logging.getLogger(__name__)

# Cache em memória para evitar query no DB a cada request.
# Formato: { user_id: (session_id, timestamp) }
# Invalidado a cada 10 segundos por user.
_session_cache = {}
_CACHE_TTL_SECONDS = 10


class SessionAwareJWTAuthentication(JWTAuthentication):
    """
    Authenticator JWT que verifica sessão única usando PostgreSQL.
    Garante que cada usuário tenha apenas uma sessão ativa por vez.
    
    Fluxo:
    1. Valida JWT normalmente
    2. Extrai X-Session-ID do header (enviado pelo frontend)
    3. Compara com session_id no banco (com cache de 10s)
    4. Se diferente → rejeita com DIFFERENT_SESSION (401)
    5. Se expirado por inatividade → rejeita com TIMEOUT (401)
    """
    
    def authenticate(self, request):
        """
        Autentica o usuário e verifica sessão única.
        """
        from core.auth_cookies import inject_bearer_from_cookie, get_session_id_from_request
        from django.db import OperationalError

        inject_bearer_from_cookie(request)
        
        # Retry logic para autenticação JWT (evitar timeout do PostgreSQL)
        max_retries = 3
        retry_delay = 1
        result = None
        
        for attempt in range(max_retries):
            try:
                result = super().authenticate(request)
                break
                
            except OperationalError as e:
                if 'timeout' in str(e).lower() and attempt < max_retries - 1:
                    logger.warning(
                        "⚠️ Timeout na autenticação JWT (tentativa %d/%d). Retrying em %ds...",
                        attempt + 1, max_retries, retry_delay
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error("❌ Falha na autenticação JWT após %d tentativas: %s", max_retries, e)
                    raise AuthenticationFailed({
                        'detail': 'Erro ao conectar ao banco de dados. Tente novamente.',
                        'code': 'database_timeout'
                    })
        
        if result is None:
            return None
        
        user, token = result
        
        # Ignorar validação de sessão para endpoints de auth (login/logout/refresh)
        if request.path.startswith('/api/auth/'):
            return user, token
        
        client_session_id = get_session_id_from_request(request)

        if not client_session_id:
            logger.warning(
                "Sessão rejeitada: X-Session-ID ausente user_id=%s path=%s",
                user.id, request.path,
            )
            raise AuthenticationFailed({
                'detail': 'Sessão inválida. Faça login novamente.',
                'code': 'NO_SESSION_HEADER',
                'message': 'Identificador de sessão ausente. Faça login novamente.',
            })
        
        # Validar sessão única com cache
        validation = self._validate_with_cache(user.id, client_session_id)
        
        if not validation['valid']:
            reason = validation.get('reason', 'UNKNOWN')
            message = validation.get('message', 'Sessão inválida')
            logger.warning(
                "🚫 Sessão bloqueada: user_id=%s reason=%s path=%s",
                user.id, reason, request.path
            )
            raise AuthenticationFailed({
                'detail': message,
                'code': reason,
                'message': message,
            })
        
        return user, token
    
    def _validate_with_cache(self, user_id: int, client_session_id: str) -> dict:
        """
        Valida sessão usando cache em memória (TTL de 10s).
        Evita query no DB a cada request.
        """
        import time as _time
        from superadmin.models import UserSession
        
        now = _time.time()
        cached = _session_cache.get(user_id)
        
        # Se cache válido, comparar direto
        if cached:
            cached_sid, cached_ts = cached
            if (now - cached_ts) < _CACHE_TTL_SECONDS:
                if cached_sid != client_session_id:
                    return {
                        'valid': False,
                        'reason': 'DIFFERENT_SESSION',
                        'message': 'Sessão encerrada — login realizado em outro dispositivo. Faça login novamente.'
                    }
                return {'valid': True}
        
        # Cache expirado ou inexistente — consultar DB
        try:
            session = UserSession.objects.filter(user_id=user_id).first()
            
            if not session:
                # Sem sessão no banco — sessão foi destruída (logout)
                _session_cache.pop(user_id, None)
                return {
                    'valid': False,
                    'reason': 'NO_SESSION',
                    'message': 'Nenhuma sessão ativa encontrada. Faça login novamente.'
                }
            
            # Verificar timeout de inatividade
            if session.is_expired(SESSION_TIMEOUT_MINUTES):
                session.delete()
                _session_cache.pop(user_id, None)
                return {
                    'valid': False,
                    'reason': 'TIMEOUT',
                    'message': f'Sessão expirou por inatividade ({SESSION_TIMEOUT_MINUTES} minutos). Faça login novamente.'
                }
            
            # Atualizar cache
            _session_cache[user_id] = (session.session_id, now)
            
            # Comparar session_id
            if session.session_id != client_session_id:
                return {
                    'valid': False,
                    'reason': 'DIFFERENT_SESSION',
                    'message': 'Sessão encerrada — login realizado em outro dispositivo. Faça login novamente.'
                }
            
            # Sessão válida — atualizar atividade (best-effort)
            try:
                session.update_activity()
            except Exception:
                pass
            
            return {'valid': True}
            
        except Exception as e:
            logger.error("session.validate_with_cache: error: %s", e)
            return {
                'valid': False,
                'reason': 'SESSION_DB_ERROR',
                'message': 'Erro ao validar sessão. Tente novamente em instantes.',
            }
