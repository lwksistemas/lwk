"""Middleware para gerenciar endpoints públicos
✅ FASE 5 v772: Consolidação de endpoints públicos
"""
import logging

logger = logging.getLogger(__name__)


class PublicEndpointsConfig:
    """Configuração centralizada de endpoints públicos
    """

    # Endpoints completamente públicos (sem autenticação)
    PUBLIC_ENDPOINTS = [
        "/api/",
        "/api/schema/",
        "/api/schema/swagger-ui/",
        "/admin/",
        "/superadmin/login/",
        "/superadmin/logout/",
        "/superadmin/token/refresh/",
        "/loja/login/",
        "/loja/logout/",
        "/suporte/login/",
        "/suporte/logout/",
        "/superadmin/lojas/info_publica/",
        "/superadmin/lojas/heartbeat/",
        "/superadmin/lojas/verificar_senha_provisoria/",
        "/mercadopago/webhook/",
        "/asaas/webhook/",
        "/health/",
    ]

    # Endpoints que permitem acesso anônimo mas também autenticado (somente DEBUG nas views)
    ALLOW_ANONYMOUS: list[str] = []

    # Endpoints de recuperação de senha
    PASSWORD_RECOVERY = [
        "/superadmin/recuperar-senha/",
        "/loja/recuperar-senha/",
        "/suporte/recuperar-senha/",
    ]

    @classmethod
    def is_public_endpoint(cls, path: str) -> bool:
        """Verifica se o endpoint é público

        Args:
            path: Caminho da URL

        Returns:
            True se for público

        """
        # Remover query string
        path = path.split("?", maxsplit=1)[0]

        # Verificar endpoints exatos
        if path in cls.PUBLIC_ENDPOINTS:
            return True

        # Verificar prefixos
        return any(path.startswith(endpoint) for endpoint in cls.PUBLIC_ENDPOINTS)

    @classmethod
    def allows_anonymous(cls, path: str) -> bool:
        """Verifica se o endpoint permite acesso anônimo

        Args:
            path: Caminho da URL

        Returns:
            True se permitir anônimo

        """
        path = path.split("?", maxsplit=1)[0]

        return any(path.startswith(endpoint) for endpoint in cls.ALLOW_ANONYMOUS)

    @classmethod
    def is_password_recovery(cls, path: str) -> bool:
        """Verifica se é endpoint de recuperação de senha

        Args:
            path: Caminho da URL

        Returns:
            True se for recuperação de senha

        """
        path = path.split("?", maxsplit=1)[0]

        return any(path.startswith(endpoint) for endpoint in cls.PASSWORD_RECOVERY)

    @classmethod
    def get_endpoint_type(cls, path: str) -> str:
        """Retorna o tipo do endpoint

        Args:
            path: Caminho da URL

        Returns:
            Tipo: 'public', 'anonymous', 'password_recovery', 'protected'

        """
        if cls.is_public_endpoint(path):
            return "public"
        if cls.allows_anonymous(path):
            return "anonymous"
        if cls.is_password_recovery(path):
            return "password_recovery"
        return "protected"

    @classmethod
    def log_endpoint_access(cls, request, endpoint_type: str):
        """Registra acesso ao endpoint

        Args:
            request: Objeto request do Django
            endpoint_type: Tipo do endpoint

        """
        user = getattr(request, "user", None)
        user_info = "Anonymous" if not user or not user.is_authenticated else user.username

        logger.info(
            f"Endpoint Access: {request.method} {request.path} | "
            f"Type: {endpoint_type} | User: {user_info} | "
            f"IP: {request.META.get('REMOTE_ADDR', 'unknown')}",
        )
