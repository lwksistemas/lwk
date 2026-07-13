"""
🛡️ RATE LIMITING CUSTOMIZADO
Throttling classes para proteger endpoints críticos
"""
import logging

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

logger = logging.getLogger(__name__)


class AuthLoginThrottle(AnonRateThrottle):
    """
    Rate limiting para login por IP.
    """
    rate = '20/minute'
    scope = 'auth_login'
    
    def allow_request(self, request, view):
        allowed = super().allow_request(request, view)
        
        if not allowed:
            logger.warning(
                f"🚨 Rate limit excedido para login: "
                f"IP={self.get_ident(request)}, "
                f"User={getattr(request.user, 'username', 'anonymous')}"
            )
        
        return allowed


class AuthRefreshThrottle(UserRateThrottle):
    """
    Rate limiting para refresh token
    10 tentativas por hora
    """
    rate = '10/hour'
    scope = 'auth_refresh'


class PasswordResetThrottle(AnonRateThrottle):
    """
    Rate limiting para reset de senha
    3 tentativas por hora
    """
    rate = '3/hour'
    scope = 'password_reset'
    
    def allow_request(self, request, view):
        allowed = super().allow_request(request, view)
        
        if not allowed:
            logger.warning(
                f"🚨 Rate limit excedido para reset de senha: "
                f"IP={self.get_ident(request)}"
            )
        
        return allowed


class BulkOperationsThrottle(UserRateThrottle):
    """
    Rate limiting para operações em lote
    10 operações por minuto
    """
    rate = '10/minute'
    scope = 'bulk_operations'


class ReportsThrottle(UserRateThrottle):
    """
    Rate limiting para geração de relatórios
    30 relatórios por hora
    """
    rate = '30/hour'
    scope = 'reports'


class StrictAnonThrottle(AnonRateThrottle):
    """
    Rate limiting para usuários anônimos - aumentado temporariamente
    500 requests por hora (para recuperar do loop infinito)
    """
    rate = '500/hour'


class RelaxedUserThrottle(UserRateThrottle):
    """
    Rate limiting relaxado para usuários autenticados
    3000 requests por hora (para suportar mais usuários)
    """
    rate = '3000/hour'


class PublicLojaCreateThrottle(AnonRateThrottle):
    """Cadastro público de loja — limite por IP."""
    rate = '5/hour'
    scope = 'public_loja_create'


class PublicLojaLookupThrottle(AnonRateThrottle):
    """Busca pública por CPF/CNPJ — limite por IP."""
    rate = '20/hour'
    scope = 'public_loja_lookup'


class DashboardRateThrottle(UserRateThrottle):
    """
    🛡️ Rate limiting específico para endpoints de dashboard
    Previne loops infinitos no frontend
    10 requisições por minuto por usuário
    """
    rate = '10/minute'
    scope = 'dashboard'
    
    def allow_request(self, request, view):
        allowed = super().allow_request(request, view)
        
        if not allowed:
            logger.warning(
                f"🚨 Rate limit excedido para dashboard: "
                f"User={getattr(request.user, 'username', 'anonymous')}, "
                f"Path={request.path}"
            )
        
        return allowed
