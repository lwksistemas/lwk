"""Views de Locais de Atendimento — Clínica da Beleza
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LocalAtendimento
from .permissions import CLINICA_RECEPCAO
from .serializers import LocalAtendimentoSerializer
from .catalogo_padrao_service import exclusivizar_padrao, garantir_primeiro_padrao
from .views_base import GetObjectMixin


class LocalAtendimentoListView(APIView):
    """GET /clinica-beleza/locais-atendimento/ — lista locais ativos da loja
    POST /clinica-beleza/locais-atendimento/ — cria novo local
    """

    permission_classes = CLINICA_RECEPCAO

    def get(self, request):
        queryset = LocalAtendimento.objects.filter(is_active=True).order_by("nome")
        return Response(LocalAtendimentoSerializer(queryset, many=True).data)

    def post(self, request):
        serializer = LocalAtendimentoSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            garantir_primeiro_padrao(LocalAtendimento, instance)
            return Response(LocalAtendimentoSerializer(instance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LocalAtendimentoDetailView(GetObjectMixin, APIView):
    """GET / PUT / DELETE /clinica-beleza/locais-atendimento/<pk>/
    """

    permission_classes = CLINICA_RECEPCAO
    model_class = LocalAtendimento
    not_found_message = "Local de atendimento não encontrado"

    def get(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        return Response(LocalAtendimentoSerializer(obj).data)

    def _update(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        serializer = LocalAtendimentoSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            instance = serializer.save()
            exclusivizar_padrao(LocalAtendimento, instance)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        return self._update(request, pk)

    def patch(self, request, pk):
        return self._update(request, pk)

    def delete(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        obj.is_active = False
        obj.save(update_fields=["is_active", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)
