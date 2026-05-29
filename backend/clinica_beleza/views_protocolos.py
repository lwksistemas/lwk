"""
Views de Protocolos de Procedimentos — Clínica da Beleza
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import ProcedureProtocol
from .serializers import ProcedureProtocolSerializer


class ProtocolListView(APIView):
    """
    GET /clinica-beleza/protocolos/?procedure=&categoria=
    POST /clinica-beleza/protocolos/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = ProcedureProtocol.objects.select_related('procedure').filter(is_active=True)
        procedure_id = request.query_params.get('procedure')
        categoria = (request.query_params.get('categoria') or '').strip()
        if procedure_id:
            try:
                queryset = queryset.filter(procedure_id=int(procedure_id))
            except (ValueError, TypeError):
                pass
        if categoria:
            queryset = queryset.filter(procedure__categoria__icontains=categoria)
        active_only = request.query_params.get('active', 'true').lower() == 'true'
        if not active_only:
            queryset = ProcedureProtocol.objects.select_related('procedure').all()
            if procedure_id:
                try:
                    queryset = queryset.filter(procedure_id=int(procedure_id))
                except (ValueError, TypeError):
                    pass
            if categoria:
                queryset = queryset.filter(procedure__categoria__icontains=categoria)
        queryset = queryset.order_by('procedure__nome', 'nome')
        return Response(ProcedureProtocolSerializer(queryset, many=True).data)

    def post(self, request):
        serializer = ProcedureProtocolSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProtocolDetailView(APIView):
    """GET / PUT / DELETE /clinica-beleza/protocolos/<id>/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            obj = ProcedureProtocol.objects.select_related('procedure').get(pk=pk)
            return Response(ProcedureProtocolSerializer(obj).data)
        except ProcedureProtocol.DoesNotExist:
            return Response({'error': 'Protocolo não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            obj = ProcedureProtocol.objects.get(pk=pk)
            serializer = ProcedureProtocolSerializer(obj, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ProcedureProtocol.DoesNotExist:
            return Response({'error': 'Protocolo não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            obj = ProcedureProtocol.objects.get(pk=pk)
            obj.is_active = False
            obj.save(update_fields=['is_active', 'updated_at'])
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProcedureProtocol.DoesNotExist:
            return Response({'error': 'Protocolo não encontrado'}, status=status.HTTP_404_NOT_FOUND)
