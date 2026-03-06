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
        """
        logger.debug(f"🔑 SessionAwareJWTAuthentication.authenticate() - Path: {request.path}")
        
        # Autenticação JWT padrão
        result = super().authenticate(request)
        
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
        
        # Validar sessão usando banco de dados
        validation = SessionManager.validate_session(user.id, token_str)
        
        if not validation['valid']:
            logger.warning(f"🚨 SESSÃO INVÁLIDA: {user.username} - Motivo: {validation['reason']}")
            raise AuthenticationFailed({
                'detail': validation['message'],
                'code': validation['reason'],
                'message': validation['message']
            })
        
        logger.debug(f"✅ Sessão válida para {user.username}")
        
        # Atualizar atividade
        SessionManager.update_activity(user.id)
        
        return user, token
