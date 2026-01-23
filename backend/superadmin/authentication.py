"""
Authenticator customizado que verifica blacklist e sessão única
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from superadmin.session_manager import SessionManager
import logging

logger = logging.getLogger(__name__)


class SessionAwareJWTAuthentication(JWTAuthentication):
    """
    Authenticator JWT que verifica sessão única e blacklist
    """
    
    def authenticate(self, request):
        """
        Autentica o usuário e verifica sessão única
        """
        # Autenticação JWT padrão
        result = super().authenticate(request)
        
        if result is None:
            return None
        
        user, token = result
        
        # Obter token string
        token_str = str(token)
        
        # Validar sessão
        validation = SessionManager.validate_session(user.id, token_str)
        
        if not validation['valid']:
            reason = validation['reason']
            message = validation['message']
            
            logger.warning(f"🚨 Sessão inválida para {user.username}: {reason}")
            
            # Lançar exceção para invalidar o token
            raise InvalidToken({
                'detail': message,
                'code': reason
            })
        
        # Atualizar atividade
        SessionManager.update_activity(user.id)
        
        return user, token
