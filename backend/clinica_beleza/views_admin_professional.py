"""
Views para habilitar/desabilitar o administrador (owner) como Profissional.

Endpoints:
- GET  /professionals/admin-status/ → estado atual do toggle
- POST /professionals/toggle-admin/ → habilitar ou desabilitar
"""
import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from superadmin.models import Loja
from .views_base import resolve_loja_id_from_request
from .admin_professional_service import (
    obter_status_admin_profissional,
    habilitar_admin_como_profissional,
    desabilitar_admin_como_profissional,
)

logger = logging.getLogger(__name__)


class AdminProfessionalStatusView(APIView):
    """GET /professionals/admin-status/ — retorna estado do toggle admin-profissional."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        loja_id = resolve_loja_id_from_request(request)
        if not loja_id:
            return Response(
                {'error': 'Loja não identificada.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            loja = Loja.objects.get(id=loja_id)
        except Loja.DoesNotExist:
            return Response(
                {'error': 'Loja não encontrada.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if loja.owner_id != request.user.id:
            return Response(
                {'error': 'Apenas o administrador da loja pode acessar este recurso.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        resultado = obter_status_admin_profissional(loja_id, request.user)
        return Response(resultado)


class AdminProfessionalToggleView(APIView):
    """POST /professionals/toggle-admin/ — habilitar ou desabilitar admin como profissional."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        loja_id = resolve_loja_id_from_request(request)
        if not loja_id:
            return Response(
                {'error': 'Loja não identificada.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            loja = Loja.objects.get(id=loja_id)
        except Loja.DoesNotExist:
            return Response(
                {'error': 'Loja não encontrada.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if loja.owner_id != request.user.id:
            return Response(
                {'error': 'Apenas o administrador da loja pode acessar este recurso.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        enable = request.data.get('enable')
        if enable is None:
            return Response(
                {'error': 'Campo "enable" é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if enable:
            professional = habilitar_admin_como_profissional(loja_id, request.user)
            return Response({
                'success': True,
                'is_enabled': True,
                'professional_id': professional.id,
            })
        else:
            desabilitar_admin_como_profissional(loja_id, request.user)
            resultado = obter_status_admin_profissional(loja_id, request.user)
            return Response({
                'success': True,
                'is_enabled': resultado['is_enabled'],
                'professional_id': resultado['professional_id'],
            })
