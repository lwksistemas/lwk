"""
View customizada para refresh token que VALIDA a sessão antes de renovar

IMPORTANTE: O refresh só funciona se a sessão atual ainda for válida.
Se outro dispositivo fez login, o refresh token deste dispositivo será recusado.
"""
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework.response import Response
from superadmin.session_manager import SessionManager
import logging

logger = logging.getLogger(__name__)


class SessionAwareTokenRefreshView(TokenRefreshView):
    """
    View de refresh token que VALIDA a sessão antes de renovar.
    
    REGRA DE SEGURANÇA:
    - Se o usuário fez login em outro dispositivo, o refresh token antigo é RECUSADO
    - Isso garante que apenas um dispositivo permaneça logado
    """
    
    def post(self, request, *args, **kwargs):
        """
        Refresh token com validação de sessão única
        """
        # 1. Extrair access token antigo do header (se disponível)
        old_access_token = None
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            old_access_token = auth_header.split(' ')[1]
        
        # 2. Decodificar o refresh token para pegar user_id ANTES de renovar
        refresh_token = request.data.get('refresh')
        if refresh_token:
            from rest_framework_simplejwt.tokens import RefreshToken
            try:
                refresh = RefreshToken(refresh_token)
                user_id = refresh['user_id']
                
                # 3. VALIDAR SESSÃO ATUAL ANTES DE RENOVAR
                # Se a sessão não é mais válida (outro login aconteceu), REJEITAR
                if old_access_token:
                    validation = SessionManager.validate_session(user_id, old_access_token)
                    
                    if not validation['valid']:
                        logger.warning(
                            f"🚫 REFRESH NEGADO: Usuário {user_id} - Motivo: {validation['reason']} - "
                            f"Outro dispositivo fez login"
                        )
                        return Response({
                            'error': 'Sessão expirada',
                            'code': validation['reason'],
                            'message': validation['message'],
                            'detail': 'Sua sessão foi encerrada porque outro login foi detectado.'
                        }, status=401)
                
            except Exception as e:
                logger.error(f"❌ Erro ao validar refresh token: {e}")
                # Continuar com o fluxo normal se houver erro na validação
        
        # 4. Chamar o refresh padrão (só se passou na validação)
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Extrair novo access token
            new_access_token = response.data.get('access')
            
            if new_access_token:
                from rest_framework_simplejwt.tokens import AccessToken
                try:
                    token = AccessToken(new_access_token)
                    user_id = token['user_id']
                    
                    logger.info(f"🔄 Refresh token bem-sucedido para usuário {user_id}")
                    
                    # Atualizar sessão no banco com novo token (mesmo dispositivo)
                    SessionManager.create_session(user_id, new_access_token)
                    
                    logger.info(f"✅ Sessão atualizada com novo token para usuário {user_id}")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao atualizar sessão no refresh: {e}")
        
        return response
