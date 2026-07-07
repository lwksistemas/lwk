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
        Processar autenticação JWT com retry em timeout do PostgreSQL.
        """
        if not hasattr(request, 'user') or request.user.is_anonymous:
            from core.retry import execute_with_db_retry
            from django.db import OperationalError

            try:
                auth_result = execute_with_db_retry(
                    lambda: self.jwt_authenticator.authenticate(request),
                    max_retries=3,
                    initial_delay=1,
                )
                if auth_result is not None:
                    user, token = auth_result
                    request.user = user
                    request.auth = token
                elif not hasattr(request, 'user'):
                    request.user = AnonymousUser()

            except (InvalidToken, TokenError):
                request.user = AnonymousUser()

            except OperationalError as e:
                logger.error("Falha na autenticação JWT após retries: %s", e)
                request.user = AnonymousUser()

            except Exception as e:
                logger.warning("Erro na autenticação JWT: %s", e)
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
            # CORS preflight: OPTIONS não envia Authorization; deve passar para o CorsMiddleware responder com 200 + headers
            if request.method == 'OPTIONS':
                return self.get_response(request)

            # Permitir apenas endpoints públicos específicos (sem autenticação)
            public_endpoints = [
                '/api/superadmin/health/',                    # Health check para failover (v750)
                '/api/superadmin/lojas/info_publica/',
                '/api/superadmin/lojas/buscar-por-documento/', # Buscar loja por CPF/CNPJ (acesso rápido)
                '/api/superadmin/lojas/por-atalho/',          # ✅ NOVO v1441: Buscar loja por atalho
                '/api/superadmin/lojas/verificar_senha_provisoria/',
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
                '/financeiro/',                      # Dados financeiros da própria loja (slug na URL)
                '/loja-financeiro/',                 # FinanceiroLojaViewSet (router: atualizar_status_asaas, etc.)
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
                
                # Permitir acesso a dados financeiros da própria loja (slug ou atalho na URL)
                elif '/loja/' in request.path and '/financeiro/' in request.path:
                    path_parts = request.path.split('/')
                    if 'loja' in path_parts:
                        loja_index = path_parts.index('loja')
                        if loja_index + 1 < len(path_parts):
                            loja_key = path_parts[loja_index + 1]
                            try:
                                from superadmin.loja_utils import resolve_loja_by_slug_or_atalho
                                loja = resolve_loja_by_slug_or_atalho(loja_key, is_active=True)
                                if not loja:
                                    return JsonResponse({
                                        'error': 'Loja não encontrada',
                                        'code': 'STORE_NOT_FOUND'
                                    }, status=404)
                                if request.user != loja.owner and not request.user.is_superuser:
                                    logger.warning(
                                        'Usuário %s tentou acessar financeiro de loja não autorizada: %s',
                                        request.user.username, loja_key,
                                    )
                                    return JsonResponse({
                                        'error': 'Acesso negado - Você só pode acessar dados da sua loja',
                                        'code': 'STORE_ACCESS_DENIED'
                                    }, status=403)
                            except Exception as e:
                                logger.error('Erro ao verificar permissões da loja: %s', e)
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
