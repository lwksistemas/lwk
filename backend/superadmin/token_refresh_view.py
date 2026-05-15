"""
View customizada para refresh token com atualização de sessão.
"""
from rest_framework_simplejwt.views import TokenRefreshView
from superadmin.session_manager import SessionManager
import logging

logger = logging.getLogger(__name__)


class SessionAwareTokenRefreshView(TokenRefreshView):
    """
    View de refresh token com atualização de sessão.
    
    REGRA: Se o refresh token é válido, SEMPRE renova.
    A sessão única é garantida no LOGIN (create_session deleta a anterior).
    Não bloqueia refresh — evita travar o app (PWA) em "Outra sessão foi iniciada".
    """
    
    def post(self, request, *args, **kwargs):
        # Chamar o refresh padrão
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            new_access_token = response.data.get('access')
            
            if new_access_token:
                from rest_framework_simplejwt.tokens import AccessToken
                try:
                    token = AccessToken(new_access_token)
                    user_id = token['user_id']
                    
                    # Atualizar sessão com novo token
                    SessionManager.create_session(user_id, new_access_token)
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao atualizar sessão no refresh: {e}")
        
        return response
