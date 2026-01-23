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
        logger.critical("🔥🔥🔥 SessionAwareJWTAuthentication.authenticate() CHAMADO")
        logger.critical(f"   Path: {request.path}")
        logger.critical(f"   Method: {request.method}")
        
        # Autenticação JWT padrão
        result = super().authenticate(request)
        
        if result is None:
            logger.critical("   ℹ️ super().authenticate() retornou None (sem token ou inválido)")
            return None
        
        user, token = result
        logger.critical(f"   ✅ JWT válido para usuário: {user.username} (ID: {user.id})")
        
        # Obter token string do access token
        token_str = str(token.token) if hasattr(token, 'token') else str(token)
        logger.critical(f"   Token extraído (50 chars): {token_str[:50]}...")
        logger.critical(f"   Token extraído (tamanho): {len(token_str)} caracteres")
        
        # Validar sessão
        logger.critical(f"   🔍 Chamando SessionManager.validate_session()...")
        validation = SessionManager.validate_session(user.id, token_str)
        
        logger.critical(f"   Resultado da validação: {validation}")
        
        if not validation['valid']:
            reason = validation['reason']
            message = validation['message']
            
            logger.critical(f"🚨🚨🚨 SESSÃO INVÁLIDA - Bloqueando acesso!")
            logger.critical(f"   Usuário: {user.username}")
            logger.critical(f"   Motivo: {reason}")
            logger.critical(f"   Mensagem: {message}")
            
            # Lançar exceção para invalidar o token
            raise InvalidToken({
                'detail': message,
                'code': reason
            })
        
        logger.critical(f"   ✅✅✅ SESSÃO VÁLIDA - Permitindo acesso")
        
        # Atualizar atividade
        SessionManager.update_activity(user.id)
        
        return user, token
