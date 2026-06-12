"""
Configuração WhatsApp centralizada — disponível para qualquer tipo de app/loja.
"""
import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .config_helpers import apply_whatsapp_config_patch, serialize_whatsapp_config
from .config_service import (
    default_whatsapp_config_payload,
    get_or_create_whatsapp_config,
    resolve_loja_from_request,
)
from .views_connection import (
    WhatsAppConnectView as BaseWhatsAppConnectView,
    WhatsAppConnectionStatusView as BaseWhatsAppConnectionStatusView,
    WhatsAppDisconnectView as BaseWhatsAppDisconnectView,
)

logger = logging.getLogger(__name__)


def _user_may_configure_whatsapp(request, loja) -> bool:
    if not request.user or not request.user.is_authenticated:
        return False
    if request.user.is_superuser:
        return True
    if loja.owner_id == request.user.id:
        return True
    return False


class WhatsAppConfigView(APIView):
    """
    GET/PATCH /api/whatsapp/config/
    Configuração WhatsApp por loja (Meta ou Evolution).
    """

    permission_classes = [IsAuthenticated]

    def _get_config(self, request):
        loja = resolve_loja_from_request(request)
        if not loja:
            logger.warning('WhatsAppConfigView: contexto de loja não encontrado')
            return None, None
        if not _user_may_configure_whatsapp(request, loja):
            return loja, 'forbidden'
        return get_or_create_whatsapp_config(loja), loja

    def get(self, request):
        config, loja = self._get_config(request)
        if loja == 'forbidden':
            return Response({'error': 'Sem permissão para configurar WhatsApp desta loja.'}, status=status.HTTP_403_FORBIDDEN)
        if config is None:
            return Response(default_whatsapp_config_payload())
        return Response(serialize_whatsapp_config(config, loja=loja, sync_evolution=True))

    def patch(self, request):
        config, loja = self._get_config(request)
        if loja == 'forbidden':
            return Response({'error': 'Sem permissão para configurar WhatsApp desta loja.'}, status=status.HTTP_403_FORBIDDEN)
        if config is None:
            return Response({'error': 'Contexto de loja não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        update_fields, err = apply_whatsapp_config_patch(config, request.data)
        if err:
            return err
        config.save(update_fields=update_fields)
        return Response(serialize_whatsapp_config(config, loja=loja))


class LojaWhatsAppConnectionStatusView(BaseWhatsAppConnectionStatusView):
    permission_classes = [IsAuthenticated]

    def _get_config(self, request):
        loja = resolve_loja_from_request(request)
        if not loja or not _user_may_configure_whatsapp(request, loja):
            return None
        return get_or_create_whatsapp_config(loja)


class LojaWhatsAppConnectView(BaseWhatsAppConnectView):
    permission_classes = [IsAuthenticated]

    def _get_config(self, request):
        loja = resolve_loja_from_request(request)
        if not loja or not _user_may_configure_whatsapp(request, loja):
            return None
        return get_or_create_whatsapp_config(loja)


class LojaWhatsAppDisconnectView(BaseWhatsAppDisconnectView):
    permission_classes = [IsAuthenticated]

    def _get_config(self, request):
        loja = resolve_loja_from_request(request)
        if not loja or not _user_may_configure_whatsapp(request, loja):
            return None
        return get_or_create_whatsapp_config(loja)
