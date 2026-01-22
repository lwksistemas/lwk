"""
Middleware de segurança para proteger rotas do superadmin
"""
from django.http import JsonResponse
from django.urls import resolve
import logging

logger = logging.getLogger(__name__)

class SuperAdminSecurityMiddleware:
    """
    Middleware que garante que apenas superusers acessem rotas do superadmin
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Verificar se é uma rota do superadmin
        if request.path.startswith('/api/superadmin/'):
            # Permitir apenas endpoints públicos específicos
            public_endpoints = [
                '/api/superadmin/lojas/info_publica/',
                '/api/superadmin/lojas/verificar_senha_provisoria/',
            ]
            
            is_public = any(request.path.startswith(endpoint) for endpoint in public_endpoints)
            
            if not is_public:
                # Verificar se o usuário é superuser
                if not request.user.is_authenticated:
                    logger.warning(f"Tentativa de acesso não autenticado ao superadmin: {request.path}")
                    return JsonResponse({
                        'error': 'Autenticação necessária',
                        'code': 'AUTHENTICATION_REQUIRED'
                    }, status=401)
                
                if not request.user.is_superuser:
                    logger.critical(f"VIOLAÇÃO DE SEGURANÇA: Usuário {request.user.username} tentou acessar {request.path}")
                    return JsonResponse({
                        'error': 'Acesso negado - Apenas superadministradores',
                        'code': 'SUPERADMIN_REQUIRED'
                    }, status=403)
        
        response = self.get_response(request)
        return response