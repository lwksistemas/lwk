"""
Views de Procedimentos — Clínica da Beleza
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Procedure
from .serializers import ProcedureSerializer
from .views_base import GetObjectMixin, map_field_names

logger = logging.getLogger(__name__)

_PROCEDURE_FIELD_MAP = {
    'name': 'nome',
    'description': 'descricao',
    'price': 'preco',
    'duration': 'duracao_minutos',
    'duration_minutes': 'duracao_minutos',
    'active': 'is_active',
    'category': 'categoria',
}


def _map_procedure_data(raw_data):
    return map_field_names(raw_data, _PROCEDURE_FIELD_MAP)


class ProcedureListView(APIView):
    """
    GET /clinica-beleza/procedures/
    POST /clinica-beleza/procedures/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_only = request.query_params.get('active', 'true').lower() == 'true'
        categoria = (request.query_params.get('categoria') or '').strip()
        queryset = Procedure.objects.all().order_by('nome')
        if active_only:
            queryset = queryset.filter(is_active=True)
        if categoria:
            queryset = queryset.filter(categoria__icontains=categoria)
        return Response(ProcedureSerializer(queryset, many=True).data)

    def post(self, request):
        data = _map_procedure_data(request.data)
        serializer = ProcedureSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error('POST procedures errors=%s', serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProcedureDetailView(GetObjectMixin, APIView):
    """GET /clinica-beleza/procedures/<id>/  PUT  DELETE"""
    permission_classes = [IsAuthenticated]
    model_class = Procedure
    not_found_message = 'Procedimento não encontrado'

    def get(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        return Response(ProcedureSerializer(obj).data)

    def put(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        data = _map_procedure_data(request.data)
        serializer = ProcedureSerializer(obj, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        obj.is_active = False
        obj.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
