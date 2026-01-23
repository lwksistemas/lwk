"""
Middleware para validação de sessão única
Valida TODAS as requisições autenticadas
"""
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from superadmin.session_manager import SessionManager
import logging

logger = logging.getLogger(__name__)


class SessionValidationMiddleware(MiddlewareMixin):
    """
    Middleware que valida sessão única em TODAS as requisições autenticadas
    """
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Valida a sessão DEPOIS da autenticação mas ANTES da view
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
        username = request.user.username
        
        logger.info(f"🔍 Validando sessão: {username} (ID: {user_id}) - Path: {request.path}")
        
        validation = SessionManager.validate_session(user_id, token)
        
        if not validation['valid']:
            reason = validation['reason']
            message = validation['message']
            
            logger.warning(f"🚨 SESSÃO INVÁLIDA: {username} - Motivo: {reason} - {message}")
            
            # Retornar erro 401 como JSON
            return JsonResponse({
                'error': message,
                'code': reason,
                'detail': 'Sua sessão foi invalidada. Faça login novamente.'
            }, status=401)
        
        # Atualizar atividade
        SessionManager.update_activity(user_id)
        
        return None
