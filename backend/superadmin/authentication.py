"""
Authenticator customizado que verifica sessão única usando banco de dados
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from superadmin.session_manager import SessionManager
import logging

logger = logging.getLogger(__name__)


class SessionAwareJWTAuthentication(JWTAuthentication):
    """
    Authenticator JWT que verifica sessão única usando PostgreSQL
    """
    
    def authenticate(self, request):
        """
        Autentica o usuário e verifica sessão única
        """
        logger.info(f"🔑 SessionAwareJWTAuthentication.authenticate() - Path: {request.path}")
        
        # Autenticação JWT padrão
        result = super().authenticate(request)
        
        if result is None:
            logger.info(f"⚠️ Autenticação JWT retornou None - Path: {request.path}")
            return None
        
        user, token = result
        
        logger.info(f"✅ JWT autenticado: {user.username} (ID: {user.id})")
        
        # Ignorar validação para endpoints de login/logout
        if request.path.startswith('/api/auth/'):
            logger.info(f"⏭️ Ignorando validação para endpoint de auth: {request.path}")
            return user, token
        
        # Extrair token string do header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token_str = auth_header.split(' ')[1]
        else:
            token_str = str(token.token) if hasattr(token, 'token') else str(token)
        
        logger.info(f"🔐 Validando sessão única: {user.username} (ID: {user.id})")
        
        # Validar sessão usando banco de dados
        validation = SessionManager.validate_session(user.id, token_str)
        
        if not validation['valid']:
            reason = validation['reason']
            message = validation['message']
            
            logger.warning(f"🚨 SESSÃO INVÁLIDA: {user.username} - Motivo: {reason}")
            
            # Lançar exceção para invalidar o token
            raise InvalidToken({
                'detail': message,
                'code': reason
            })
        
        logger.info(f"✅ Sessão válida para {user.username}")
        
        # Atualizar atividade
        SessionManager.update_activity(user.id)
        
        return user, token
