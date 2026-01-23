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
        
        # Ignorar validação para endpoints de login/logout
        if request.path.startswith('/api/auth/'):
            return user, token
        
        # Extrair token string do header (mais confiável)
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token_str = auth_header.split(' ')[1]
        else:
            # Fallback: tentar extrair do objeto token
            token_str = str(token.token) if hasattr(token, 'token') else str(token)
        
        logger.info(f"🔐 Authenticator validando sessão: {user.username} (ID: {user.id}) - Path: {request.path}")
        
        # Validar sessão
        validation = SessionManager.validate_session(user.id, token_str)
        
        if not validation['valid']:
            reason = validation['reason']
            message = validation['message']
            
            logger.warning(f"🚨 SESSÃO INVÁLIDA no Authenticator: {user.username} - Motivo: {reason}")
            
            # Lançar exceção para invalidar o token
            raise InvalidToken({
                'detail': message,
                'code': reason
            })
        
        # Atualizar atividade
        SessionManager.update_activity(user.id)
        
        return user, token
