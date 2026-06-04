"""
View customizada para refresh token.
Renova JWT e atualiza cookie httpOnly quando habilitado.
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenRefreshView
import logging

from core.auth_cookies import (
    attach_auth_cookies,
    get_refresh_from_request,
    use_httponly_jwt_cookies,
)

logger = logging.getLogger(__name__)


class SessionAwareTokenRefreshView(TokenRefreshView):
    """Refresh token — não altera sessão no banco."""

    def post(self, request, *args, **kwargs):
        refresh = None
        if hasattr(request.data, 'get'):
            refresh = request.data.get('refresh')
        if not refresh:
            refresh = get_refresh_from_request(request)
        if not refresh:
            return Response(
                {'detail': 'Refresh token é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TokenRefreshSerializer(data={'refresh': refresh})
        try:
            valid = serializer.is_valid()
        except TokenError:
            valid = False
        if not valid:
            logger.debug('refresh token inválido ou expirado')
            return Response(
                {
                    'detail': 'Token inválido ou expirado.',
                    'code': 'token_not_valid',
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        response = Response(serializer.validated_data, status=status.HTTP_200_OK)

        access = serializer.validated_data.get('access')
        if use_httponly_jwt_cookies() and access:
            new_refresh = serializer.validated_data.get('refresh', refresh)
            attach_auth_cookies(
                response,
                access=access,
                refresh=new_refresh or refresh,
            )
        return response
