"""
Views de conexão WhatsApp Web (Evolution) — reutilizadas por Clínica e CRM.
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .connection_service import (
    disconnect_evolution,
    reset_evolution_connection,
    start_evolution_connection,
    sync_evolution_connection,
)
from .evolution_client import EvolutionAPIError
from .models import WhatsAppConfig


class WhatsAppConnectionMixin:
    """Mixin que exige _get_config(request) -> WhatsAppConfig | None."""

    def _connection_payload(self, config, fetch_qr=False):
        if getattr(config, 'whatsapp_provider', WhatsAppConfig.PROVIDER_META) != WhatsAppConfig.PROVIDER_EVOLUTION:
            return {
                'provider': config.whatsapp_provider,
                'connection_status': config.whatsapp_connection_status,
                'connected_phone': (config.whatsapp_connected_phone or '').strip(),
                'connected_at': config.whatsapp_connected_at.isoformat() if config.whatsapp_connected_at else None,
                'qr_base64': None,
                'error': None,
            }
        return sync_evolution_connection(config, fetch_qr=fetch_qr)


class WhatsAppConnectionStatusView(WhatsAppConnectionMixin, APIView):
    """GET — status da conexão WhatsApp Web (+ QR se pendente)."""

    def get(self, request):
        config = self._get_config(request)
        if config == 'forbidden':
            return Response(
                {'error': 'Sem permissão para configurar WhatsApp desta loja.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if config is None:
            return Response({'error': 'Contexto de loja não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        fetch_qr = request.query_params.get('qr', '').lower() in ('1', 'true', 'yes')
        return Response(self._connection_payload(config, fetch_qr=fetch_qr))


class WhatsAppConnectView(WhatsAppConnectionMixin, APIView):
    """POST — inicia conexão WhatsApp Web (gera QR)."""

    def post(self, request):
        config = self._get_config(request)
        if config == 'forbidden':
            return Response(
                {'error': 'Sem permissão para configurar WhatsApp desta loja.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if config is None:
            return Response({'error': 'Contexto de loja não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        try:
            payload = start_evolution_connection(config)
            return Response(payload)
        except EvolutionAPIError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


class WhatsAppDisconnectView(WhatsAppConnectionMixin, APIView):
    """POST — desconecta WhatsApp Web."""

    def post(self, request):
        config = self._get_config(request)
        if config == 'forbidden':
            return Response(
                {'error': 'Sem permissão para configurar WhatsApp desta loja.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if config is None:
            return Response({'error': 'Contexto de loja não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        try:
            payload = disconnect_evolution(config)
            return Response(payload)
        except EvolutionAPIError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


class WhatsAppResetSessionView(WhatsAppConnectionMixin, APIView):
    """POST — apaga sessão Evolution corrompida e gera novo QR Code."""

    def post(self, request):
        config = self._get_config(request)
        if config == 'forbidden':
            return Response(
                {'error': 'Sem permissão para configurar WhatsApp desta loja.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if config is None:
            return Response({'error': 'Contexto de loja não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        try:
            payload = reset_evolution_connection(config)
            return Response(payload)
        except EvolutionAPIError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
