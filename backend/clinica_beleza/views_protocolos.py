"""Views de Protocolos de Procedimentos — Clínica da Beleza
"""
from contextlib import suppress
from decimal import Decimal

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.utils.dateparse import parse_datetime

from .agenda_service import AgendaValidationError
from .models import (
    LocalAtendimento,
    Patient,
    Procedure,
    ProcedureProtocol,
    ProdutoEstoque,
    Professional,
    ProtocoloContrato,
)
from .pagination import paginate_queryset
from .permissions import (
    CLINICA_AGENDA,
    CLINICA_CLINICAL,
    CLINICA_RECEPCAO,
    professional_id_do_usuario,
    resolve_agenda_professional_scope,
    _loja_and_profissional,
)
from .protocolo_comercial import FORMAS_COBRANCA, ProtocoloAgendaConflito, agendar_protocolo
from .protocolo_personalizado import (
    agendar_protocolo_personalizado,
    criar_protocolo_personalizado,
)
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


class ProtocoloPersonalizadoOpcoesView(APIView):
    """GET /clinica-beleza/protocolos/personalizados/opcoes/?patient="""

    permission_classes = CLINICA_CLINICAL

    def get(self, request):
        patient = _buscar(Patient, request.query_params.get("patient"), "Cliente não encontrada.")
        if isinstance(patient, Response):
            return patient
        from .convenio_service import resolver_preco_procedimento

        convenio = patient.convenio if getattr(patient, "convenio_id", None) and patient.convenio.is_active else None
        procedimentos = []
        for procedure in Procedure.objects.filter(is_active=True).order_by("nome"):
            preco = resolver_preco_procedimento(convenio, procedure)
            procedimentos.append({
                "id": procedure.id,
                "nome": procedure.nome,
                "preco": str(Decimal(str(preco or 0)).quantize(Decimal("0.01"))),
            })
        return Response({
            "profissional_id": _profissional_fixo(request),
            "profissionais": [
                {"id": item.id, "nome": item.nome}
                for item in Professional.objects.filter(is_active=True).order_by("nome")
            ],
            "locais": [
                {"id": item.id, "nome": item.nome}
                for item in LocalAtendimento.objects.filter(is_active=True).order_by("nome")
            ],
            "procedimentos": procedimentos,
            "produtos": [
                {"id": item.id, "nome": item.nome, "unidade_medida": item.unidade_medida}
                for item in ProdutoEstoque.objects.filter(is_active=True).order_by("nome")
            ],
        })


class ProtocoloPersonalizadoCreateView(APIView):
    """POST /clinica-beleza/protocolos/personalizados/"""

    permission_classes = CLINICA_CLINICAL

    def post(self, request):
        data = request.data or {}
        patient = _buscar(Patient, data.get("patient"), "Cliente não encontrada.")
        if isinstance(patient, Response):
            return patient
        try:
            procedimentos = _procedimentos_do_pedido(data.get("procedimentos"))
            produtos = _produtos_do_pedido(data.get("produtos"))
            resultado = criar_protocolo_personalizado(
                patient=patient,
                procedimentos=procedimentos,
                produtos=produtos,
                desconto_tipo=str(data.get("desconto_tipo") or "").strip(),
                desconto_valor=data.get("desconto_valor") or 0,
                sessoes=int(data.get("sessoes") or 0),
                intervalo_quantidade=int(data.get("intervalo_quantidade") or 0),
                intervalo_unidade=str(data.get("intervalo_unidade") or "").strip(),
                tempo_minutos=int(data.get("tempo_minutos") or 0),
                nome=str(data.get("nome") or ""),
                request=request,
            )
        except (TypeError, ValueError):
            return Response({"detail": "Revise sessões, intervalo, duração e desconto."}, status=status.HTTP_400_BAD_REQUEST)
        except AgendaValidationError as exc:
            return Response({"detail": exc.message}, status=status.HTTP_400_BAD_REQUEST)
        return Response(resultado, status=status.HTTP_201_CREATED)


class ProtocoloPersonalizadoPendentesView(APIView):
    """GET /clinica-beleza/protocolos/personalizados/pendentes/?patient="""

    permission_classes = CLINICA_AGENDA

    def get(self, request):
        from django.db.models import Count

        patient = _buscar(Patient, request.query_params.get("patient"), "Cliente não encontrada.")
        if isinstance(patient, Response):
            return patient
        contratos = (
            ProtocoloContrato.objects.filter(patient=patient, protocol__isnull=True)
            .annotate(sessoes_na_agenda=Count("agendamentos"))
            .filter(sessoes_na_agenda=0)
            .order_by("-created_at")
        )
        return Response([
            {
                "id": item.id,
                "nome": item.nome or "Protocolo personalizado",
                "sessoes": item.sessoes,
                "intervalo_quantidade": item.intervalo_quantidade,
                "intervalo_unidade": item.intervalo_unidade,
                "tempo_minutos": item.tempo_minutos,
                "valor_total": str(item.valor_total),
            }
            for item in contratos
        ])


class ProtocoloPersonalizadoAgendarView(APIView):
    """POST /clinica-beleza/protocolos/personalizados/<id>/agendar/"""

    permission_classes = CLINICA_AGENDA

    def post(self, request, pk):
        data = request.data or {}
        try:
            contrato = ProtocoloContrato.objects.select_related("patient", "patient__convenio").get(
                pk=pk,
                protocol__isnull=True,
            )
        except ProtocoloContrato.DoesNotExist:
            return Response({"detail": "Protocolo não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        scope = resolve_agenda_professional_scope(request)
        professional_id = data.get("professional")
        if scope is not None:
            if scope and str(professional_id or scope) != str(scope):
                return Response(
                    {"detail": "Você só pode agendar na sua agenda."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            professional_id = scope
        professional = _buscar(Professional, professional_id, "Profissional não encontrada.")
        local = _buscar(LocalAtendimento, data.get("local_atendimento"), "Local de atendimento não encontrado.")
        for item in (professional, local):
            if isinstance(item, Response):
                return item
        inicio = parse_datetime(str(data.get("data_inicio") or ""))
        if inicio is None:
            return Response(
                {"detail": "Informe a data e a hora da primeira sessão."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            resultado = agendar_protocolo_personalizado(
                contrato=contrato,
                professional=professional,
                local_atendimento=local,
                data_inicio=inicio,
                request=request,
            )
        except AgendaValidationError as exc:
            return Response({"detail": exc.message}, status=status.HTTP_400_BAD_REQUEST)
        return Response(resultado, status=status.HTTP_201_CREATED)


def _profissional_fixo(request):
    """A profissional grava o protocolo no próprio nome. Admin escolhe."""
    _loja, prof = _loja_and_profissional(request)
    if prof in (None, "superuser"):
        return None
    if getattr(prof, "perfil", None) == "profissional":
        return professional_id_do_usuario(request)
    return None


def _procedimentos_do_pedido(raw):
    if not isinstance(raw, list) or not raw:
        raise AgendaValidationError("Inclua ao menos um procedimento.")
    ids = []
    for item in raw:
        ids.append(int(item))
    encontrados = {item.id: item for item in Procedure.objects.filter(pk__in=ids)}
    procedimentos = []
    for pk in ids:
        procedure = encontrados.get(pk)
        if procedure is None:
            raise AgendaValidationError("Procedimento não encontrado.")
        procedimentos.append(procedure)
    return procedimentos


def _produtos_do_pedido(raw):
    if not raw:
        return []
    if not isinstance(raw, list):
        raise AgendaValidationError("Revise os produtos de cada sessão.")
    ids = [int(item.get("produto_id")) for item in raw]
    encontrados = {item.id: item for item in ProdutoEstoque.objects.filter(pk__in=ids)}
    produtos = []
    for item in raw:
        produto = encontrados.get(int(item.get("produto_id")))
        if produto is None:
            raise AgendaValidationError("Produto não encontrado.")
        produtos.append({"produto": produto, "quantidade": item.get("quantidade")})
    return produtos


def _buscar(model, raw_id, mensagem):
    try:
        pk = int(raw_id)
    except (TypeError, ValueError):
        return Response({"detail": mensagem}, status=status.HTTP_400_BAD_REQUEST)
    try:
        return model.objects.get(pk=pk)
    except model.DoesNotExist:
        return Response({"detail": mensagem}, status=status.HTTP_400_BAD_REQUEST)
