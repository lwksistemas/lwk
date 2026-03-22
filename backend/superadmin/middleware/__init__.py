"""
Middleware do Superadmin
✅ FASE 5 v772: Middlewares organizados
"""
from django.http import JsonResponse
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
import logging

from .public_endpoints import PublicEndpointsConfig
from .enhanced_logging import (
    EnhancedLoggingMiddleware,
    PerformanceMonitoringMiddleware,
    SecurityHeadersMiddleware
)

logger = logging.getLogger(__name__)


class JWTAuthenticationMiddleware:
    """
    Middleware que processa autenticação JWT para todas as requisições
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_authenticator = JWTAuthentication()
    
    def __call__(self, request):
        """
        Processar autenticação JWT com retry logic
        ✅ FIX v916: Retry logic para evitar timeout do PostgreSQL
        """
        if not hasattr(request, 'user') or request.user.is_anonymous:
            from django.db import OperationalError
            import time
            
            max_retries = 3
            retry_delay = 1
            
            for attempt in range(max_retries):
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
                    break  # Sucesso, sair do loop
                    
                except (InvalidToken, TokenError):
                    # Token inválido, manter usuário anônimo
                    request.user = AnonymousUser()
                    break
                    
                except OperationalError as e:
                    if 'timeout' in str(e).lower() and attempt < max_retries - 1:
                        logger.warning(
                            f"⚠️ Timeout na autenticação JWT (tentativa {attempt + 1}/{max_retries}). "
                            f"Tentando novamente em {retry_delay}s..."
                        )
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        logger.error(f"❌ Falha na autenticação JWT após {max_retries} tentativas: {e}")
                        request.user = AnonymousUser()
                        break
                        
                except Exception as e:
                    # Qualquer outro erro, manter usuário anônimo
                    logger.warning(f"Erro na autenticação JWT: {e}")
                    request.user = AnonymousUser()
                    break
        
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
            # CORS preflight: OPTIONS não envia Authorization; deve passar para o CorsMiddleware responder com 200 + headers
            if request.method == 'OPTIONS':
                return self.get_response(request)

            # Permitir apenas endpoints públicos específicos (sem autenticação)
            public_endpoints = [
                '/api/superadmin/health/',                    # Health check para failover (v750)
                '/api/superadmin/lojas/info_publica/',
                '/api/superadmin/lojas/verificar_senha_provisoria/',
                '/api/superadmin/lojas/debug_senha_status/',
                '/api/superadmin/usuarios/recuperar_senha/',  # Recuperação de senha superadmin/suporte
                '/api/superadmin/lojas/recuperar_senha/',     # Recuperação de senha lojas
                '/api/superadmin/mercadopago-webhook/',       # Webhook Mercado Pago (notificações de pagamento)
                '/api/superadmin/public/',                    # ✅ NOVO: Rotas públicas para cadastro de lojas
            ]
            
            # Endpoints que proprietários/usuários da loja podem acessar (com autenticação)
            # A view (IsLojaOwner) verifica se é owner da loja do pagamento
            owner_allowed_patterns = [
                '/alterar_senha_primeiro_acesso/',  # Trocar senha provisória
                '/reenviar_senha/',                  # Reenviar senha por email
                '/financeiro/',                      # Dados financeiros da própria loja
                '/loja-pagamentos/',                 # baixar_boleto_pdf, gerar_pix (IsLojaOwner)
                '/exportar_backup/',                 # Backup: exportar (loja)
                '/enviar_backup_agora/',             # Backup: enviar por email agora
                '/importar_backup/',                 # Backup: importar (loja)
                '/configuracao_backup/',             # Backup: config GET
                '/atualizar_configuracao_backup/',   # Backup: config PATCH/PUT
                '/historico_backups/',               # Backup: histórico
                '/reenviar_backup_email/',           # Backup: reenviar email
            ]
            
            is_public = any(request.path.startswith(endpoint) for endpoint in public_endpoints)
            
            # POST para criar loja (cadastro público) - permitir sem autenticação
            if request.path == '/api/superadmin/lojas/' and request.method == 'POST':
                is_public = True
            
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


__all__ = [
    'PublicEndpointsConfig',
    'EnhancedLoggingMiddleware',
    'PerformanceMonitoringMiddleware',
    'SecurityHeadersMiddleware',
    'JWTAuthenticationMiddleware',
    'SuperAdminSecurityMiddleware',
]
