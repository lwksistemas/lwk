"""
Middleware para validação de sessão única
Valida TODAS as requisições autenticadas
"""
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status
from superadmin.session_manager import SessionManager
import logging

logger = logging.getLogger(__name__)


class SessionValidationMiddleware(MiddlewareMixin):
    """
    Middleware que valida sessão única em TODAS as requisições autenticadas
    """
    
    def process_request(self, request):
        """
        Valida a sessão antes de processar a requisição
        """
        # Ignorar requisições não autenticadas
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
        
        # Ignorar requisições de login/logout
        if request.path.startswith('/api/auth/'):
            return None
        
        # Ignorar requisições OPTIONS (CORS)
        if request.method == 'OPTIONS':
            return None
        
        # Tentar extrair o token JWT do header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        # Validar sessão
        user_id = request.user.id
        validation = SessionManager.validate_session(user_id, token)
        
        if not validation['valid']:
            reason = validation['reason']
            message = validation['message']
            
            logger.warning(f"🚨 Sessão inválida para {request.user.username}: {reason}")
            
            # Retornar erro 401
            return Response({
                'error': message,
                'code': reason,
                'detail': 'Sua sessão foi invalidada. Faça login novamente.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Atualizar atividade
        SessionManager.update_activity(user_id)
        
        return None
