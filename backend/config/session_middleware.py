"""
Middleware de Controle de Sessão Única
Valida sessões e atualiza atividade do usuário
"""
from django.http import JsonResponse
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from superadmin.session_manager import SessionManager
import logging

logger = logging.getLogger(__name__)


class SessionControlMiddleware:
    """
    Middleware que:
    1. Valida se o usuário tem sessão ativa
    2. Verifica se não há outra sessão em outro dispositivo
    3. Atualiza timestamp de atividade
    4. Faz logout automático após 30 minutos de inatividade
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_authenticator = JWTAuthentication()
    
    def __call__(self, request):
        # Processar autenticação JWT
        self._authenticate_jwt(request)
        
        # Verificar controle de sessão
        violation = self._check_session_control(request)
        if violation:
            return violation
        
        response = self.get_response(request)
        return response
    
    def _authenticate_jwt(self, request):
        """Processa autenticação JWT"""
        if not hasattr(request, 'user') or request.user.is_anonymous:
            try:
                auth_result = self.jwt_authenticator.authenticate(request)
                if auth_result is not None:
                    user, token = auth_result
                    request.user = user
                    request.auth = token
                else:
                    if not hasattr(request, 'user'):
                        request.user = AnonymousUser()
            except (InvalidToken, TokenError):
                request.user = AnonymousUser()
            except Exception as e:
                logger.warning(f"Erro na autenticação JWT: {e}")
                request.user = AnonymousUser()
    
    def _check_session_control(self, request):
        """
        Verifica controle de sessão única
        """
        path = request.path
        
        # Rotas públicas (sem controle de sessão)
        public_routes = [
            '/api/auth/token/',  # Login
            '/api/auth/token/refresh/',  # Refresh token
            '/api/auth/superadmin/login/',  # Login superadmin
            '/api/auth/suporte/login/',  # Login suporte
            '/api/auth/loja/login/',  # Login loja
            '/api/superadmin/lojas/info_publica/',  # Info pública de lojas
            '/admin/',  # Django admin
        ]
        
        # Verificar se é rota pública
        if any(path.startswith(route) for route in public_routes):
            return None
        
        # Verificar se usuário está autenticado
        if not request.user or not request.user.is_authenticated:
            return None  # Deixar outros middlewares tratarem
        
        # Obter token da requisição
        token = self._get_token_from_request(request)
        if not token:
            logger.warning(f"⚠️ Requisição sem token para {path}")
            return None
        
        # Validar sessão
        user_id = request.user.id
        username = request.user.username
        
        logger.info(f"🔒 MIDDLEWARE - Validando sessão para {username} (ID: {user_id})")
        logger.info(f"   Path: {path}")
        
        validation = SessionManager.validate_session(user_id, token)
        
        if not validation['valid']:
            reason = validation['reason']
            message = validation['message']
            
            logger.warning(f"🚨 SESSÃO INVÁLIDA - Usuário {username} (ID: {user_id})")
            logger.warning(f"   Motivo: {reason}")
            logger.warning(f"   Mensagem: {message}")
            
            # Mensagens específicas por motivo
            if reason == 'DIFFERENT_SESSION' or reason == 'BLACKLISTED':
                return JsonResponse({
                    'error': 'Sessão inválida',
                    'code': 'SESSION_CONFLICT',
                    'message': 'Você foi desconectado porque iniciou uma nova sessão em outro dispositivo.',
                    'action': 'FORCE_LOGOUT'
                }, status=401)
            
            elif reason == 'TIMEOUT':
                return JsonResponse({
                    'error': 'Sessão expirada',
                    'code': 'SESSION_TIMEOUT',
                    'message': f'Sua sessão expirou por inatividade ({SessionManager.SESSION_TIMEOUT_MINUTES} minutos sem uso).',
                    'action': 'FORCE_LOGOUT'
                }, status=401)
            
            elif reason == 'NO_SESSION':
                return JsonResponse({
                    'error': 'Sessão não encontrada',
                    'code': 'NO_SESSION',
                    'message': 'Nenhuma sessão ativa encontrada. Faça login novamente.',
                    'action': 'FORCE_LOGOUT'
                }, status=401)
        
        # Sessão válida - atualizar atividade
        logger.info(f"✅ SESSÃO VÁLIDA - Atualizando atividade de {username}")
        SessionManager.update_activity(user_id)
        
        return None  # Sem violação
    
    def _get_token_from_request(self, request):
        """Extrai o token JWT da requisição"""
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]  # Remove 'Bearer '
        return None
