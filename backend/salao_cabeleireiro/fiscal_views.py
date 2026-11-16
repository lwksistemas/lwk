"""Configuração da nota de serviço e do cupom de produto do salão."""
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from clinica_beleza.nfse_config_service import test_issnet_connection
from tenants.middleware import get_current_loja_id

from .fiscal_serializers import SalaoNFSeConfigSerializer
from .fiscal_service import SalaoFiscalErro, gravar_nfce, obter_nfce, obter_nfse, publico_nfce
from .permissions import IsSalaoAdmin


class SalaoNFSeConfigView(APIView):
    permission_classes = [IsSalaoAdmin]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response({"detail": "Loja não identificada."}, status=400)
        config = obter_nfse(loja_id)
        return Response(SalaoNFSeConfigSerializer(config, context={"request": request, "loja_id": loja_id}).data)

    def patch(self, request):
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response({"detail": "Loja não identificada."}, status=400)
        config = obter_nfse(loja_id)
        serializer = SalaoNFSeConfigSerializer(
            config, data=request.data, partial=True, context={"request": request, "loja_id": loja_id},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SalaoNFSeTesteView(APIView):
    permission_classes = [IsSalaoAdmin]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request):
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response({"detail": "Loja não identificada."}, status=400)
        resultado = test_issnet_connection(request, obter_nfse(loja_id))
        codigo = status.HTTP_200_OK if resultado.get("success") else status.HTTP_400_BAD_REQUEST
        return Response(resultado, status=codigo)


class SalaoNfceConfigView(APIView):
    permission_classes = [IsSalaoAdmin]

    def get(self, request):
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response({"detail": "Loja não identificada."}, status=400)
        return Response(publico_nfce(obter_nfce(loja_id)))

    def put(self, request):
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response({"detail": "Loja não identificada."}, status=400)
        config = obter_nfce(loja_id)
        try:
            gravar_nfce(config, request.data)
        except SalaoFiscalErro as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(publico_nfce(config))
