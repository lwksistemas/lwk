"""Views de Protocolos de Procedimentos — Clínica da Beleza
"""
from contextlib import suppress

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ProcedureProtocol
from .pagination import paginate_queryset
from .permissions import CLINICA_RECEPCAO
from .serializers import ProcedureProtocolSerializer
from .views_base import GetObjectMixin


class ProtocolListView(APIView):
    """GET /clinica-beleza/protocolos/?procedure=&categoria=&active=true
    POST /clinica-beleza/protocolos/
    """

    permission_classes = CLINICA_RECEPCAO

    def get(self, request):
        active_only = request.query_params.get("active", "true").lower() == "true"
        queryset = ProcedureProtocol.objects.select_related("procedure")
        if active_only:
            queryset = queryset.filter(is_active=True)
        procedure_id = request.query_params.get("procedure")
        if procedure_id:
            with suppress(ValueError, TypeError):
                queryset = queryset.filter(procedure_id=int(procedure_id))
        categoria = (request.query_params.get("categoria") or "").strip()
        if categoria:
            queryset = queryset.filter(procedure__categoria__icontains=categoria)
        return paginate_queryset(
            queryset.order_by("procedure__nome", "nome"),
            request,
            ProcedureProtocolSerializer,
        )

    def post(self, request):
        serializer = ProcedureProtocolSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProtocolDetailView(GetObjectMixin, APIView):
    """GET / PUT / DELETE /clinica-beleza/protocolos/<id>/"""

    permission_classes = CLINICA_RECEPCAO
    model_class = ProcedureProtocol
    not_found_message = "Protocolo não encontrado"
    select_related_fields = ["procedure"]

    def get(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        return Response(ProcedureProtocolSerializer(obj).data)

    def put(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        serializer = ProcedureProtocolSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        obj.is_active = False
        obj.save(update_fields=["is_active", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)
