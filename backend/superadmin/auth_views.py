"""
Views customizadas de autenticação com controle de sessão
"""
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.response import Response
from rest_framework import status
from superadmin.session_manager import SessionManager
import logging

logger = logging.getLogger(__name__)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer customizado que adiciona informações extras ao token"""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Adicionar informações extras ao token
        token['username'] = user.username
        token['email'] = user.email
        token['is_superuser'] = user.is_superuser
        
        return token


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    View customizada de login que:
    1. Gera tokens JWT
    2. Cria sessão única para o usuário
    3. Invalida sessões anteriores
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        # Obter tokens normalmente
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Login bem-sucedido
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')
            
            # Obter usuário
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.user
            
            # Criar sessão única
            session_id = SessionManager.create_session(user.id, access_token)
            
            # Adicionar informações de sessão na resposta
            response.data['session_id'] = session_id
            response.data['session_timeout_minutes'] = SessionManager.SESSION_TIMEOUT_MINUTES
            response.data['user'] = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_superuser': user.is_superuser,
            }
            
            logger.info(f"✅ Login bem-sucedido: {user.username} (ID: {user.id})")
            logger.info(f"   Sessão criada: {session_id}")
            
        return response


class LogoutView(TokenObtainPairView):
    """
    View de logout que destrói a sessão do usuário
    """
    
    def post(self, request, *args, **kwargs):
        if request.user and request.user.is_authenticated:
            user_id = request.user.id
            username = request.user.username
            
            # Destruir sessão
            SessionManager.destroy_session(user_id)
            
            logger.info(f"👋 Logout: {username} (ID: {user_id})")
            
            return Response({
                'message': 'Logout realizado com sucesso',
                'code': 'LOGOUT_SUCCESS'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'error': 'Usuário não autenticado',
            'code': 'NOT_AUTHENTICATED'
        }, status=status.HTTP_401_UNAUTHORIZED)
