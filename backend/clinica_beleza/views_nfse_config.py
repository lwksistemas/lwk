"""
Views para configuração de NFS-e da Clínica da Beleza (per-loja).
GET/PATCH /api/clinica-beleza/nfse-config/
POST /api/clinica-beleza/nfse-config/test-issnet/
"""
import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework import status

from tenants.middleware import get_current_loja_id
from .models import ClinicaBelezaNFSeConfig
from .serializers.nfse_config import ClinicaBelezaNFSeConfigSerializer
from .nfse_config_service import (
    get_or_create_nfse_config,
    test_issnet_connection,
)

logger = logging.getLogger(__name__)


class NFSeConfigView(APIView):
    """GET/PATCH da configuração de NFS-e individual da loja."""
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response({'detail': 'Loja não identificada.'}, status=400)

        config = get_or_create_nfse_config(loja_id)
        serializer = ClinicaBelezaNFSeConfigSerializer(config, context={'request': request, 'loja_id': loja_id})
        return Response(serializer.data)

    def patch(self, request):
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response({'detail': 'Loja não identificada.'}, status=400)

        config = get_or_create_nfse_config(loja_id)
        serializer = ClinicaBelezaNFSeConfigSerializer(
            config, data=request.data, partial=True,
            context={'request': request, 'loja_id': loja_id},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NFSeConfigTestISSNetView(APIView):
    """POST - Testa conexão com o WebService ISSNet."""
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request):
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response({'detail': 'Loja não identificada.'}, status=400)

        config = get_or_create_nfse_config(loja_id)
        result = test_issnet_connection(request, config)
        http_status = status.HTTP_200_OK if result.get('success') else status.HTTP_400_BAD_REQUEST
        return Response(result, status=http_status)
