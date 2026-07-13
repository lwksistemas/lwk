"""Endpoints para o owner habilitar/desabilitar-se como profissional."""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from superadmin.models import Loja

from .admin_professional_service import (
    desabilitar_admin_como_profissional,
    habilitar_admin_como_profissional,
    obter_status_admin_profissional,
)
from .permissions import CLINICA_ADMIN
from .serializers import ProfessionalSerializer
from .utils import LojaContextHelper
from .views_base import resolve_loja_id_from_request


def _verificar_owner(request, loja_id: int):
    if not request.user or not request.user.is_authenticated:
        return Response({'detail': 'Autenticação necessária.'}, status=status.HTTP_401_UNAUTHORIZED)
    loja = Loja.objects.using('default').filter(id=loja_id, is_active=True).first()
    if not loja:
        return Response({'detail': 'Loja não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    if loja.owner_id != request.user.id:
        return Response({'detail': 'Somente o administrador da loja pode alterar esta configuração.'}, status=status.HTTP_403_FORBIDDEN)
    return None


class AdminProfessionalStatusView(APIView):
    """GET /professionals/admin-status/"""

    permission_classes = CLINICA_ADMIN

    def get(self, request):
        loja_id = resolve_loja_id_from_request(request)
        if not loja_id:
            return Response({'detail': 'Loja não identificada.'}, status=status.HTTP_400_BAD_REQUEST)
        denied = _verificar_owner(request, loja_id)
        if denied:
            return denied
        data = obter_status_admin_profissional(loja_id, request.user)
        return Response(data)


class AdminProfessionalToggleView(APIView):
    """POST /professionals/toggle-admin/  body: { "enable": true|false }"""

    permission_classes = CLINICA_ADMIN

    def post(self, request):
        loja_id = resolve_loja_id_from_request(request)
        if not loja_id:
            return Response({'detail': 'Loja não identificada.'}, status=status.HTTP_400_BAD_REQUEST)
        denied = _verificar_owner(request, loja_id)
        if denied:
            return denied

        enable = request.data.get('enable')
        if enable is None:
            return Response({'detail': 'Informe enable: true ou false.'}, status=status.HTTP_400_BAD_REQUEST)
        enable = enable in (True, 'true', '1', 1)

        try:
            if enable:
                prof = habilitar_admin_como_profissional(loja_id, request.user)
                admin_ids = LojaContextHelper.get_admin_professional_ids()
                serializer = ProfessionalSerializer(prof, context={'admin_professional_ids': admin_ids})
                return Response({'success': True, 'is_enabled': True, 'professional': serializer.data})
            desabilitar_admin_como_profissional(loja_id, request.user)
            return Response({'success': True, 'is_enabled': False})
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
