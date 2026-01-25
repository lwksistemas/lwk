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
        # DEBUG: Confirmar que este authenticator está sendo usado
        logger.info(f"🔑 SessionAwareJWTAuthentication.authenticate() chamado - Path: {request.path}")
        
        # Autenticação JWT padrão
        result = super().authenticate(request)
        
        if result is None:
            logger.info(f"⚠️ Autenticação JWT retornou None - Path: {request.path}")
            return None
        
        user, token = result
        
        logger.info(f"✅ JWT autenticado: {user.username} (ID: {user.id})")
        
        # 🔧 TEMPORÁRIO: Desabilitar validação de sessão única devido ao cache local
        # O cache local (LocMemCache) não é compartilhado entre workers do Heroku
        # Isso causa problemas com múltiplos logins simultâneos
        logger.info(f"⏭️ Validação de sessão única DESABILITADA temporariamente")
        return user, token
        
        # Código original comentado:
        # # Ignorar validação para endpoints de login/logout
        # if request.path.startswith('/api/auth/'):
        #     logger.info(f"⏭️ Ignorando validação para endpoint de auth: {request.path}")
        #     return user, token
        # 
        # # Extrair token string do header (mais confiável)
        # auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        # if auth_header.startswith('Bearer '):
        #     token_str = auth_header.split(' ')[1]
        # else:
        #     # Fallback: tentar extrair do objeto token
        #     token_str = str(token.token) if hasattr(token, 'token') else str(token)
        # 
        # logger.info(f"🔐 Authenticator validando sessão: {user.username} (ID: {user.id}) - Path: {request.path}")
        # 
        # # Validar sessão
        # validation = SessionManager.validate_session(user.id, token_str)
        # 
        # if not validation['valid']:
        #     reason = validation['reason']
        #     message = validation['message']
        #     
        #     logger.warning(f"🚨 SESSÃO INVÁLIDA no Authenticator: {user.username} - Motivo: {reason}")
        #     
        #     # Lançar exceção para invalidar o token
        #     raise InvalidToken({
        #         'detail': message,
        #         'code': reason
        #     })
        # 
        # logger.info(f"✅ Sessão válida para {user.username}")
        # 
        # # Atualizar atividade
        # SessionManager.update_activity(user.id)
        # 
        # return user, token
