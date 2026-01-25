"""
View customizada para refresh token que atualiza a sessão no banco
"""
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken
from superadmin.session_manager import SessionManager
import logging

logger = logging.getLogger(__name__)


class SessionAwareTokenRefreshView(TokenRefreshView):
    """
    View de refresh token que atualiza a sessão no banco de dados
    """
    
    def post(self, request, *args, **kwargs):
        """
        Refresh token e atualiza sessão no banco
        """
        # Chamar o refresh padrão
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Extrair novo access token
            new_access_token = response.data.get('access')
            
            if new_access_token:
                # Decodificar token para pegar user_id
                from rest_framework_simplejwt.tokens import AccessToken
                try:
                    token = AccessToken(new_access_token)
                    user_id = token['user_id']
                    
                    logger.info(f"🔄 Refresh token bem-sucedido para usuário {user_id}")
                    
                    # Atualizar sessão no banco com novo token
                    SessionManager.create_session(user_id, new_access_token)
                    
                    logger.info(f"✅ Sessão atualizada com novo token para usuário {user_id}")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao atualizar sessão no refresh: {e}")
        
        return response
