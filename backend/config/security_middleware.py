"""
Middleware de Segurança - Isolamento Total dos 3 Grupos de Usuários

GRUPO 1: Super Admin - Acesso exclusivo ao /superadmin/
GRUPO 2: Suporte - Acesso exclusivo ao /suporte/
GRUPO 3: Lojas - Acesso exclusivo à própria loja

Cada grupo tem banco de dados isolado e não pode acessar dados de outros grupos.
"""
from django.http import JsonResponse
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
import logging

logger = logging.getLogger(__name__)


class SecurityIsolationMiddleware:
    """
    Middleware que garante isolamento total entre os 3 grupos de usuários:
    1. Super Admin (banco: db_superadmin.sqlite3)
    2. Suporte (banco: db_suporte.sqlite3)
    3. Lojas (banco: db_loja_{slug}.sqlite3)
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_authenticator = JWTAuthentication()
    
    def __call__(self, request):
        # 1. Processar autenticação JWT
        self._authenticate_jwt(request)
        
        # 2. Verificar isolamento de rotas
        violation = self._check_route_isolation(request)
        if violation:
            return violation
        
        # 3. Verificar isolamento de dados de loja
        violation = self._check_store_isolation(request)
        if violation:
            return violation
        
        response = self.get_response(request)
        return response
    
    def _authenticate_jwt(self, request):
        """
        Processa autenticação JWT com retry logic
        ✅ FIX v916: Retry logic para evitar timeout do PostgreSQL
        """
        if not hasattr(request, 'user') or request.user.is_anonymous:
            from django.db import OperationalError
            import time
            
            max_retries = 3
            retry_delay = 1
            
            for attempt in range(max_retries):
                try:
                    auth_result = self.jwt_authenticator.authenticate(request)
                    if auth_result is not None:
                        user, token = auth_result
                        request.user = user
                        request.auth = token
                    else:
                        if not hasattr(request, 'user'):
                            request.user = AnonymousUser()
                    break  # Sucesso, sair do loop
                    
                except (InvalidToken, TokenError):
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
                    logger.warning(f"Erro na autenticação JWT: {e}")
                    request.user = AnonymousUser()
                    break
    
    def _check_route_isolation(self, request):
        """
        Verifica isolamento de rotas entre os 3 grupos
        
        REGRAS:
        - Super Admin: APENAS /api/superadmin/ (exceto endpoints públicos específicos)
        - Suporte: APENAS /api/suporte/
        - Lojas: APENAS /api/{tipo_loja}/ da própria loja
        """
        path = request.path
        
        # ========================================
        # GRUPO 1: SUPER ADMIN
        # ========================================
        if path.startswith('/api/superadmin/'):
            # Endpoints públicos (sem autenticação)
            public_endpoints = [
                '/api/superadmin/lojas/info_publica/',
                '/api/superadmin/lojas/verificar_senha_provisoria/',
                '/api/superadmin/lojas/debug_senha_status/',
                '/api/superadmin/mercadopago-webhook/',  # Webhook MP (notificações de pagamento)
                '/api/superadmin/public/',  # ✅ NOVO: Rotas públicas para cadastro de lojas
            ]
            
            if any(path.startswith(endpoint) for endpoint in public_endpoints):
                return None  # Permitir acesso público
            
            # POST para criar loja (cadastro público)
            if path == '/api/superadmin/lojas/' and request.method == 'POST':
                return None  # Permitir cadastro público
            
            # Verificar autenticação
            if not request.user or not request.user.is_authenticated:
                logger.warning(f"❌ VIOLAÇÃO: Acesso não autenticado ao superadmin: {path}")
                return JsonResponse({
                    'error': 'Autenticação necessária',
                    'code': 'AUTHENTICATION_REQUIRED',
                    'grupo_requerido': 'superadmin'
                }, status=401)

            # Heartbeat (sessão única / useSessionMonitor): qualquer usuário autenticado
            # (dono, vendedor CRM, suporte, superadmin). A view usa IsAuthenticated apenas.
            if path.rstrip('/').endswith('/heartbeat') or '/lojas/heartbeat' in path:
                return None
            
            # Endpoints permitidos para proprietários de lojas (acessar seus próprios dados)
            owner_allowed_patterns = [
                '/alterar_senha_primeiro_acesso/',
                '/reenviar_senha/',
                '/financeiro/',
                '/loja-pagamentos/',  # baixar_boleto_pdf, gerar_pix, etc. (IsLojaOwner verifica)
            ]
            
            is_owner_allowed = any(pattern in path for pattern in owner_allowed_patterns)
            
            if is_owner_allowed:
                # Proprietário de loja pode acessar seus próprios dados
                # A view fará a verificação específica
                logger.info(f"✅ Acesso de proprietário permitido: {request.user.username} -> {path}")
                return None
            
            # Para outras rotas, APENAS superuser
            if not request.user.is_superuser:
                logger.critical(f"🚨 VIOLAÇÃO DE SEGURANÇA: Usuário {request.user.username} (grupo: {self._get_user_group(request.user)}) tentou acessar superadmin: {path}")
                return JsonResponse({
                    'error': 'Acesso negado - Apenas Super Administradores',
                    'code': 'SUPERADMIN_REQUIRED',
                    'seu_grupo': self._get_user_group(request.user),
                    'grupo_requerido': 'superadmin'
                }, status=403)
        
        # ========================================
        # GRUPO 2: SUPORTE
        # ========================================
        elif path.startswith('/api/suporte/'):
            # Verificar autenticação
            if not request.user or not request.user.is_authenticated:
                logger.warning(f"❌ VIOLAÇÃO: Acesso não autenticado ao suporte: {path}")
                return JsonResponse({
                    'error': 'Autenticação necessária',
                    'code': 'AUTHENTICATION_REQUIRED',
                    'grupo_requerido': 'suporte'
                }, status=401)
            
            # Verificar se é usuário de suporte ou superadmin
            user_group = self._get_user_group(request.user)
            
            if user_group not in ['suporte', 'superadmin']:
                logger.critical(f"🚨 VIOLAÇÃO DE SEGURANÇA: Usuário {request.user.username} (grupo: {user_group}) tentou acessar suporte: {path}")
                return JsonResponse({
                    'error': 'Acesso negado - Apenas usuários de Suporte',
                    'code': 'SUPORTE_REQUIRED',
                    'seu_grupo': user_group,
                    'grupo_requerido': 'suporte'
                }, status=403)
        
        # ========================================
        # GRUPO 3: LOJAS
        # ========================================
        elif self._is_store_route(path):
            # Verificar autenticação
            if not request.user or not request.user.is_authenticated:
                logger.warning(f"❌ VIOLAÇÃO: Acesso não autenticado à loja: {path}")
                return JsonResponse({
                    'error': 'Autenticação necessária',
                    'code': 'AUTHENTICATION_REQUIRED',
                    'grupo_requerido': 'loja'
                }, status=401)
            
            # Verificar se é proprietário de loja (SUPERADMIN NÃO PODE ACESSAR)
            user_group = self._get_user_group(request.user)
            
            if user_group != 'loja':
                logger.critical(f"🚨 VIOLAÇÃO DE SEGURANÇA: Usuário {request.user.username} (grupo: {user_group}) tentou acessar loja: {path}")
                return JsonResponse({
                    'error': 'Acesso negado - Apenas proprietários de lojas podem acessar',
                    'code': 'STORE_OWNER_REQUIRED',
                    'seu_grupo': user_group,
                    'grupo_requerido': 'loja',
                    'mensagem': 'Super Admin e Suporte não podem acessar áreas de lojas'
                }, status=403)
        
        return None  # Sem violação
    
    def _check_store_isolation(self, request):
        """
        Verifica se proprietário de loja está tentando acessar dados de outra loja
        
        REGRA CRÍTICA: Uma loja NUNCA pode acessar dados de outra loja
        """
        if not request.user or not request.user.is_authenticated:
            return None
        
        # SUPERADMIN NÃO DEVE ACESSAR ROTAS DE LOJAS
        if request.user.is_superuser and self._is_store_route(request.path):
            logger.critical(f"🚨 VIOLAÇÃO CRÍTICA: Super Admin {request.user.username} tentou acessar rota de loja: {request.path}")
            return JsonResponse({
                'error': 'Super Admin não pode acessar áreas de lojas',
                'code': 'SUPERADMIN_CANNOT_ACCESS_STORES',
                'mensagem': 'Use o painel de Super Admin para gerenciar lojas'
            }, status=403)
        
        user_group = self._get_user_group(request.user)
        if user_group != 'loja':
            return None
        
        # Verificar se está tentando acessar dados de loja
        if self._is_store_route(request.path):
            # Extrair slug da loja da URL ou header
            requested_store_slug = self._extract_store_slug(request)
            
            if requested_store_slug:
                # Verificar se o usuário é proprietário DESTA loja (suporta múltiplas lojas por dono)
                try:
                    from superadmin.models import Loja
                    user_owns_this_store = Loja.objects.filter(
                        owner=request.user, is_active=True, slug=requested_store_slug
                    ).exists()
                    if not user_owns_this_store:
                        user_lojas_slugs = list(
                            Loja.objects.filter(owner=request.user, is_active=True).values_list('slug', flat=True)
                        )
                        logger.critical(
                            "🚨 VIOLAÇÃO CRÍTICA: Usuário %s (lojas: %s) tentou acessar loja: %s",
                            request.user.username, user_lojas_slugs, requested_store_slug
                        )
                        return JsonResponse({
                            'error': 'Acesso negado - Você só pode acessar suas próprias lojas',
                            'code': 'CROSS_STORE_ACCESS_DENIED',
                            'loja_solicitada': requested_store_slug
                        }, status=403)
                    
                except Exception as e:
                    logger.error(f"Erro ao verificar isolamento de loja: {e}")
                    return JsonResponse({
                        'error': 'Erro ao verificar permissões',
                        'code': 'PERMISSION_CHECK_ERROR'
                    }, status=500)
        
        return None  # Sem violação
    
    def _get_user_group(self, user):
        """
        Identifica o grupo do usuário
        
        Retorna: 'superadmin', 'suporte', 'loja', ou 'unknown'
        """
        if not user or not user.is_authenticated:
            return 'unknown'
        
        # Super Admin
        if user.is_superuser:
            return 'superadmin'
        
        # Verificar se é usuário de suporte
        try:
            from superadmin.models import UsuarioSistema
            usuario_sistema = UsuarioSistema.objects.filter(user=user, is_active=True).first()
            if usuario_sistema:
                if usuario_sistema.tipo == 'suporte':
                    return 'suporte'
                elif usuario_sistema.tipo == 'superadmin':
                    return 'superadmin'
        except:
            pass
        
        # Verificar se é proprietário de loja
        try:
            from superadmin.models import Loja
            if Loja.objects.filter(owner=user, is_active=True).exists():
                return 'loja'
        except:
            pass
        
        return 'unknown'
    
    def _is_store_route(self, path):
        """Verifica se a rota é de uma loja"""
        store_routes = [
            '/api/clinica/',
            '/api/crm/',
            '/api/ecommerce/',
            '/api/restaurante/',
            '/api/servicos/',
            '/api/stores/',
            '/api/products/',
        ]
        return any(path.startswith(route) for route in store_routes)
    
    def _extract_store_slug(self, request):
        """
        Extrai o slug da loja da requisição.
        Compatível com o frontend: X-Tenant-Slug, X-Loja-ID (resolve para slug), X-Store-Slug, query e path.
        """
        # 1. Headers (frontend envia X-Tenant-Slug e X-Loja-ID)
        store_slug = (
            request.headers.get('X-Store-Slug')
            or request.headers.get('X-Tenant-Slug')
        )
        if store_slug:
            return store_slug.strip()
        loja_id = request.headers.get('X-Loja-ID')
        if loja_id:
            try:
                from superadmin.models import Loja
                loja = Loja.objects.filter(id=int(loja_id), is_active=True).first()
                if loja:
                    return loja.slug
            except (ValueError, TypeError):
                pass
        # 2. Query
        store_slug = request.GET.get('store') or request.GET.get('tenant')
        if store_slug:
            return store_slug.strip()
        # 3. Path: /api/.../loja/{slug}/...
        path_parts = request.path.split('/')
        if 'loja' in path_parts:
            loja_index = path_parts.index('loja')
            if loja_index + 1 < len(path_parts):
                return path_parts[loja_index + 1]
        return None
