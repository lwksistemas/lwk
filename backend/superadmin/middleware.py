"""
Middleware de segurança para proteger rotas do superadmin
"""
from django.http import JsonResponse
from django.urls import resolve
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
import logging

logger = logging.getLogger(__name__)

class JWTAuthenticationMiddleware:
    """
    Middleware que processa autenticação JWT para todas as requisições
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_authenticator = JWTAuthentication()
    
    def __call__(self, request):
        # Processar autenticação JWT se não houver usuário autenticado
        if not hasattr(request, 'user') or request.user.is_anonymous:
            try:
                # Tentar autenticar via JWT
                auth_result = self.jwt_authenticator.authenticate(request)
                if auth_result is not None:
                    user, token = auth_result
                    request.user = user
                    request.auth = token
                else:
                    # Se não há token JWT, manter usuário anônimo
                    if not hasattr(request, 'user'):
                        request.user = AnonymousUser()
            except (InvalidToken, TokenError) as e:
                # Token inválido, manter usuário anônimo
                request.user = AnonymousUser()
            except Exception as e:
                # Qualquer outro erro, manter usuário anônimo
                logger.warning(f"Erro na autenticação JWT: {e}")
                request.user = AnonymousUser()
        
        response = self.get_response(request)
        return response

class SuperAdminSecurityMiddleware:
    """
    Middleware que garante que apenas superusers acessem rotas do superadmin
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Verificar se é uma rota do superadmin
        if request.path.startswith('/api/superadmin/'):
            # Permitir apenas endpoints públicos específicos (sem autenticação)
            public_endpoints = [
                '/api/superadmin/lojas/info_publica/',
                '/api/superadmin/lojas/verificar_senha_provisoria/',
                '/api/superadmin/lojas/debug_senha_status/',
                '/api/superadmin/usuarios/recuperar_senha/',  # Recuperação de senha superadmin/suporte
                '/api/superadmin/lojas/recuperar_senha/',     # Recuperação de senha lojas
            ]
            
            # Endpoints que proprietários de lojas podem acessar (com autenticação)
            # Esses endpoints têm verificação adicional na view para garantir que o usuário é o proprietário
            owner_allowed_patterns = [
                '/alterar_senha_primeiro_acesso/',  # Trocar senha provisória
                '/reenviar_senha/',                  # Reenviar senha por email
                '/financeiro/',                      # Dados financeiros da própria loja
            ]
            
            is_public = any(request.path.startswith(endpoint) for endpoint in public_endpoints)
            is_owner_allowed = any(pattern in request.path for pattern in owner_allowed_patterns)
            
            if not is_public:
                # Verificar autenticação
                if not hasattr(request, 'user') or not request.user.is_authenticated:
                    logger.warning(f"Tentativa de acesso não autenticado ao superadmin: {request.path}")
                    return JsonResponse({
                        'error': 'Autenticação necessária',
                        'code': 'AUTHENTICATION_REQUIRED'
                    }, status=401)
                
                # Se é um endpoint permitido para owners, deixar a view fazer a verificação específica
                if is_owner_allowed:
                    # A view fará a verificação de permissão (IsOwnerOrSuperAdmin ou verificação manual)
                    logger.info(f"Acesso de proprietário permitido: {request.user.username} -> {request.path}")
                    pass
                
                # Permitir acesso a dados financeiros da própria loja para administradores
                elif '/loja/' in request.path and '/financeiro/' in request.path:
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
                                if request.user == loja.owner:
                                    # Usuário é owner da loja, permitir acesso aos dados financeiros
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
                
                # Heartbeat: qualquer usuário autenticado (superadmin ou loja) para monitor de sessão única
                elif request.path.rstrip('/').endswith('heartbeat'):
                    pass  # View usa IsAuthenticated
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