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
                # Verificar se o usuário existe e está autenticado
                if not hasattr(request, 'user') or not request.user.is_authenticated:
                    logger.warning(f"Tentativa de acesso não autenticado ao superadmin: {request.path}")
                    return JsonResponse({
                        'error': 'Autenticação necessária',
                        'code': 'AUTHENTICATION_REQUIRED'
                    }, status=401)
                
                # Permitir acesso a dados financeiros da própria loja para administradores
                if '/loja/' in request.path and '/financeiro/' in request.path:
                    # Extrair slug da loja da URL
                    path_parts = request.path.split('/')
                    if 'loja' in path_parts:
                        loja_index = path_parts.index('loja')
                        if loja_index + 1 < len(path_parts):
                            loja_slug = path_parts[loja_index + 1]
                            
                            # Verificar se o usuário é admin da loja específica
                            try:
                                from stores.models import Store
                                loja = Store.objects.get(slug=loja_slug)
                                if request.user == loja.admin_user:
                                    # Usuário é admin da loja, permitir acesso aos dados financeiros
                                    pass
                                elif not request.user.is_superuser:
                                    logger.warning(f"Usuário {request.user.username} tentou acessar dados financeiros de loja não autorizada: {loja_slug}")
                                    return JsonResponse({
                                        'error': 'Acesso negado - Você só pode acessar dados da sua loja',
                                        'code': 'STORE_ACCESS_DENIED'
                                    }, status=403)
                            except Store.DoesNotExist:
                                logger.warning(f"Tentativa de acesso a loja inexistente: {loja_slug}")
                                return JsonResponse({
                                    'error': 'Loja não encontrada',
                                    'code': 'STORE_NOT_FOUND'
                                }, status=404)
                            except Exception as e:
                                logger.error(f"Erro ao verificar permissões da loja: {e}")
                                return JsonResponse({
                                    'error': 'Erro interno do servidor',
                                    'code': 'INTERNAL_ERROR'
                                }, status=500)
                
                # Para outras rotas do superadmin, exigir superuser
                elif not request.user.is_superuser:
                    logger.critical(f"VIOLAÇÃO DE SEGURANÇA: Usuário {request.user.username} tentou acessar {request.path}")
                    return JsonResponse({
                        'error': 'Acesso negado - Apenas superadministradores',
                        'code': 'SUPERADMIN_REQUIRED'
                    }, status=403)
        
        # IMPORTANTE: Não interferir com outras rotas (auth, clinica, etc.)
        response = self.get_response(request)
        return response