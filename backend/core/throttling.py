"""
🛡️ RATE LIMITING CUSTOMIZADO
Throttling classes para proteger endpoints críticos
"""
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
import logging

logger = logging.getLogger(__name__)


class AuthLoginThrottle(UserRateThrottle):
    """
    Rate limiting para login - muito restritivo
    5 tentativas a cada 15 minutos
    """
    rate = '5/15min'
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
    rate = '10/min'
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
    Rate limiting estrito para usuários anônimos
    50 requests por hora
    """
    rate = '50/hour'


class RelaxedUserThrottle(UserRateThrottle):
    """
    Rate limiting relaxado para usuários autenticados
    3000 requests por hora (para suportar mais usuários)
    """
    rate = '3000/hour'
