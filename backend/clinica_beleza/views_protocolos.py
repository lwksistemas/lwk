"""Views de Protocolos de Procedimentos — Clínica da Beleza
"""
from contextlib import suppress

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.utils.dateparse import parse_datetime

from .agenda_service import AgendaValidationError
from .models import LocalAtendimento, Patient, ProcedureProtocol, ProdutoEstoque, Professional
from .pagination import paginate_queryset
from .permissions import CLINICA_RECEPCAO
from .protocolo_comercial import FORMAS_COBRANCA, ProtocoloAgendaConflito, agendar_protocolo
from .serializers import ProcedureProtocolSerializer
from .views_base import GetObjectMixin


class ProtocolListView(APIView):
    """GET /clinica-beleza/protocolos/?procedure=&categoria=&active=true
    POST /clinica-beleza/protocolos/
    """

    permission_classes = CLINICA_RECEPCAO

    def get(self, request):
        active_only = request.query_params.get("active", "true").lower() == "true"
        queryset = ProcedureProtocol.objects.select_related("procedure").prefetch_related(
            "produtos__produto",
        )
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


class ProtocolProdutosOpcoesView(APIView):
    """GET /clinica-beleza/protocolos/produtos/ — produtos ativos para o cadastro do protocolo."""

    permission_classes = CLINICA_RECEPCAO

    def get(self, request):
        produtos = ProdutoEstoque.objects.filter(is_active=True).order_by("nome")
        return Response(
            [
                {"id": item.id, "nome": item.nome, "unidade_medida": item.unidade_medida}
                for item in produtos
            ]
        )


class ProtocolAgendarView(GetObjectMixin, APIView):
    """POST /clinica-beleza/protocolos/<id>/agendar/"""

    permission_classes = CLINICA_RECEPCAO
    model_class = ProcedureProtocol
    not_found_message = "Protocolo não encontrado"
    select_related_fields = ["procedure"]

    def post(self, request, pk):
        protocol, error = self.object_or_404(pk)
        if error:
            return error
        data = request.data or {}
        forma = (data.get("forma_cobranca") or "").strip()
        if forma not in FORMAS_COBRANCA:
            return Response(
                {"detail": "Escolha pagar por consulta ou o valor total."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        inicio = parse_datetime(str(data.get("data_inicio") or ""))
        if inicio is None:
            return Response(
                {"detail": "Informe a data e a hora da primeira sessão."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        patient = _buscar(Patient, data.get("patient"), "Paciente não encontrado.")
        professional = _buscar(Professional, data.get("professional"), "Profissional não encontrado.")
        local = _buscar(LocalAtendimento, data.get("local_atendimento"), "Local de atendimento não encontrado.")
        for item in (patient, professional, local):
            if isinstance(item, Response):
                return item
        try:
            resultado = agendar_protocolo(
                protocol=protocol,
                patient=patient,
                professional=professional,
                local_atendimento=local,
                data_inicio=inicio,
                forma_cobranca=forma,
                request=request,
            )
        except ProtocoloAgendaConflito as exc:
            return Response(
                {"detail": str(exc), "conflitos": exc.conflitos},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except AgendaValidationError as exc:
            return Response({"detail": exc.message}, status=status.HTTP_400_BAD_REQUEST)
        return Response(resultado, status=status.HTTP_201_CREATED)


def _buscar(model, raw_id, mensagem):
    try:
        pk = int(raw_id)
    except (TypeError, ValueError):
        return Response({"detail": mensagem}, status=status.HTTP_400_BAD_REQUEST)
    try:
        return model.objects.get(pk=pk)
    except model.DoesNotExist:
        return Response({"detail": mensagem}, status=status.HTTP_400_BAD_REQUEST)
