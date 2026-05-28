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
    data = raw_data.copy() if hasattr(raw_data, 'copy') else dict(raw_data)
    for en, pt in _PROCEDURE_FIELD_MAP.items():
        if en in data and pt not in data:
            data[pt] = data.pop(en)
    return data


class ProcedureListView(APIView):
    """
    GET /clinica-beleza/procedures/
    POST /clinica-beleza/procedures/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_only = request.query_params.get('active', 'true').lower() == 'true'
        queryset = Procedure.objects.all().order_by('nome')
        if active_only:
            queryset = queryset.filter(is_active=True)
        return Response(ProcedureSerializer(queryset, many=True).data)

    def post(self, request):
        data = _map_procedure_data(request.data)
        serializer = ProcedureSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error('POST procedures errors=%s', serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProcedureDetailView(APIView):
    """GET /clinica-beleza/procedures/<id>/  PUT  DELETE"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            return Response(ProcedureSerializer(Procedure.objects.get(pk=pk)).data)
        except Procedure.DoesNotExist:
            return Response({'error': 'Procedimento não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            obj = Procedure.objects.get(pk=pk)
            data = _map_procedure_data(request.data)
            serializer = ProcedureSerializer(obj, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Procedure.DoesNotExist:
            return Response({'error': 'Procedimento não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            obj = Procedure.objects.get(pk=pk)
            obj.is_active = False
            obj.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Procedure.DoesNotExist:
            return Response({'error': 'Procedimento não encontrado'}, status=status.HTTP_404_NOT_FOUND)
