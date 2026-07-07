"""
Views de Autenticação com Isolamento Total e Validação de Grupo
"""
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from core.throttling import AuthLoginThrottle
from core.auth_cookies import attach_auth_cookies, clear_auth_cookies
from core.audit import registrar_evento_seguranca
from core.login_lockout import check_account_locked, record_login_failure, clear_login_failures
from core.store_membership import resolve_loja_for_user, user_belongs_to_store
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from superadmin.session_manager import SessionManager
from superadmin.models import Loja, UsuarioSistema, ProfissionalUsuario, VendedorUsuario
from django.db import connection
from django.db.utils import OperationalError
import logging

logger = logging.getLogger(__name__)


def authenticate_with_retry(username, password, max_retries=3):
    """
    Autenticar com retry em caso de timeout de conexão.

    Args:
        username: Nome de usuário
        password: Senha
        max_retries: Número máximo de tentativas (padrão: 3)

    Returns:
        User object ou None
    """
    from core.retry import retry_on_db_timeout

    @retry_on_db_timeout(max_retries=max_retries, initial_delay=0.5)
    def _do_authenticate():
        connection.ensure_connection()
        return authenticate(username=username, password=password)

    return _do_authenticate()



class SecureLoginView(APIView):
    """
    View de login segura com validação de grupo e endpoint.

    Delega toda a lógica para LoginService (service layer).
    
    REGRAS:
    - /api/auth/superadmin/login/ - Apenas superadmin
    - /api/auth/suporte/login/ - Apenas suporte
    - /api/auth/loja/login/ - Apenas proprietários de loja
    """
    permission_classes = [AllowAny]
    throttle_classes = [AuthLoginThrottle]

    def post(self, request, user_type=None):
        from superadmin.services.login_service import LoginService

        result = LoginService().execute(request, user_type)
        response = Response(result.data, status=result.status_code)

        if result.success and result.cookies:
            return attach_auth_cookies(
                response,
                access=result.cookies['access'],
                refresh=result.cookies['refresh'],
                session_id=result.cookies['session_id'],
            )
        return response


class SecureLogoutView(APIView):
    """View de logout segura"""
    
    def post(self, request):
        if request.user and request.user.is_authenticated:
            user_id = request.user.id
            username = request.user.username
            
            # Destruir sessão
            SessionManager.destroy_session(user_id)
            
            logger.info(f"👋 Logout: {username} (ID: {user_id})")
            
            response = Response({
                'message': 'Logout realizado com sucesso',
                'code': 'LOGOUT_SUCCESS'
            }, status=status.HTTP_200_OK)
            return clear_auth_cookies(response)

        response = Response({
            'error': 'Usuário não autenticado',
            'code': 'NOT_AUTHENTICATED'
        }, status=status.HTTP_401_UNAUTHORIZED)
        return clear_auth_cookies(response)


class BeaconLogoutView(APIView):
    """
    View de logout via sendBeacon (ao fechar aba do navegador)
    
    Esta view é especial porque:
    - Aceita requisições sem header de autenticação
    - Recebe o token no body da requisição
    - Usa navigator.sendBeacon() que não permite headers customizados
    """
    permission_classes = [AllowAny]
    throttle_classes = [AuthLoginThrottle]  # Rate limit: 20/min por IP
    
    def post(self, request):
        """
        Logout via beacon - aceita token no body
        """
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import TokenError
        
        token_str = request.data.get('token')
        
        if not token_str:
            logger.warning("🚪 Beacon logout: token não fornecido")
            return Response({
                'error': 'Token não fornecido',
                'code': 'NO_TOKEN'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Decodificar token para obter user_id
            token = AccessToken(token_str)
            user_id = token['user_id']
            
            # Destruir sessão
            SessionManager.destroy_session(user_id)
            
            logger.info(f"🚪 Beacon logout: Usuário {user_id} deslogado (aba fechada)")
            
            return Response({
                'message': 'Logout via beacon realizado',
                'code': 'BEACON_LOGOUT_SUCCESS'
            }, status=status.HTTP_200_OK)
            
        except TokenError as e:
            logger.warning(f"🚪 Beacon logout: token inválido - {e}")
            return Response({
                'error': 'Token inválido',
                'code': 'INVALID_TOKEN'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"🚪 Beacon logout: erro - {e}")
            return Response({
                'error': 'Erro ao processar logout',
                'code': 'LOGOUT_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
