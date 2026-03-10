"""
Authenticator customizado que verifica sessão única usando banco de dados
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from superadmin.session_manager import SessionManager
import logging

logger = logging.getLogger(__name__)


class SessionAwareJWTAuthentication(JWTAuthentication):
    """
    Authenticator JWT que verifica sessão única usando PostgreSQL
    Garante que cada usuário tenha apenas uma sessão ativa por vez
    """
    
    def authenticate(self, request):
        """
        Autentica o usuário e verifica sessão única
        ✅ FIX: Retry logic para evitar timeout do PostgreSQL
        """
        from django.db import OperationalError
        import time
        
        logger.debug(f"🔑 SessionAwareJWTAuthentication.authenticate() - Path: {request.path}")
        
        # ✅ FIX: Retry logic para autenticação JWT
        max_retries = 3
        retry_delay = 1  # segundos
        result = None
        
        for attempt in range(max_retries):
            try:
                # Autenticação JWT padrão
                result = super().authenticate(request)
                break  # Sucesso, sair do loop
                
            except OperationalError as e:
                if 'timeout' in str(e).lower() and attempt < max_retries - 1:
                    logger.warning(
                        f"⚠️ Timeout na autenticação JWT (tentativa {attempt + 1}/{max_retries}). "
                        f"Tentando novamente em {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Backoff exponencial
                else:
                    logger.error(f"❌ Falha na autenticação JWT após {max_retries} tentativas: {e}")
                    raise AuthenticationFailed({
                        'detail': 'Erro ao conectar ao banco de dados. Tente novamente.',
                        'code': 'database_timeout'
                    })
        
        if result is None:
            return None
        
        user, token = result
        logger.debug(f"✅ JWT autenticado: {user.username} (ID: {user.id})")
        
        # Ignorar validação para endpoints de login/logout
        if request.path.startswith('/api/auth/'):
            return user, token
        
        # Extrair token string do header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        token_str = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else str(token.token) if hasattr(token, 'token') else str(token)
        
        logger.debug(f"🔐 Validando sessão única: {user.username} (ID: {user.id})")
        
        # ✅ FIX: Retry logic para validação de sessão
        validation = None
        for attempt in range(max_retries):
            try:
                # Validar sessão usando banco de dados
                validation = SessionManager.validate_session(user.id, token_str)
                break  # Sucesso, sair do loop
                
            except OperationalError as e:
                if 'timeout' in str(e).lower() and attempt < max_retries - 1:
                    logger.warning(
                        f"⚠️ Timeout na validação de sessão (tentativa {attempt + 1}/{max_retries}). "
                        f"Tentando novamente em {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error(f"❌ Falha na validação de sessão após {max_retries} tentativas: {e}")
                    raise AuthenticationFailed({
                        'detail': 'Erro ao validar sessão. Tente novamente.',
                        'code': 'database_timeout'
                    })
        
        if validation and not validation['valid']:
            logger.warning(f"🚨 SESSÃO INVÁLIDA: {user.username} - Motivo: {validation['reason']}")
            raise AuthenticationFailed({
                'detail': validation['message'],
                'code': validation['reason'],
                'message': validation['message']
            })
        
        logger.debug(f"✅ Sessão válida para {user.username}")
        
        # Atualizar atividade (best-effort, não falha se der timeout)
        try:
            SessionManager.update_activity(user.id)
        except OperationalError:
            logger.warning(f"⚠️ Timeout ao atualizar atividade do usuário {user.username}")
        
        return user, token
