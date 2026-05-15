"""
View customizada para refresh token.
Apenas renova o JWT — não mexe na sessão (evita race condition).
"""
from rest_framework_simplejwt.views import TokenRefreshView
import logging

logger = logging.getLogger(__name__)


class SessionAwareTokenRefreshView(TokenRefreshView):
    """
    View de refresh token — apenas renova o JWT.
    NÃO atualiza a sessão no banco (evita race condition com múltiplos refreshes simultâneos).
    A sessão é criada/atualizada apenas no LOGIN.
    """
    pass
