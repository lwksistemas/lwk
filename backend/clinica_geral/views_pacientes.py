from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import HasLojaAccess
from core.views import BaseModelViewSet
from tenants.middleware import ensure_loja_context

from .models import Evolucao, Paciente, PacienteAnexo, Prescricao
from .paciente_service import arquivar_paciente, listar_pacientes
from .serializers import (
    EvolucaoSerializer,
    PacienteAnexoSerializer,
    PacienteListaSerializer,
    PacienteSerializer,
    PrescricaoSerializer,
)


class PacienteViewSet(BaseModelViewSet):
    serializer_class = PacienteSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return PacienteListaSerializer
        return PacienteSerializer

    def get_queryset(self):
        ensure_loja_context(self.request)
        return listar_pacientes(
            self.request.query_params.get("letra") or "",
            self.request.query_params.get("q") or "",
        )

    def perform_destroy(self, instance):
        arquivar_paciente(instance)


class PacienteAnexoViewSet(BaseModelViewSet):
    serializer_class = PacienteAnexoSerializer

    def get_queryset(self):
        ensure_loja_context(self.request)
        qs = PacienteAnexo.objects.select_related("paciente")
        paciente_id = self.request.query_params.get("paciente")
        if paciente_id:
            qs = qs.filter(paciente_id=paciente_id)
        return qs


class ProntuarioPacienteView(APIView):
    permission_classes = [IsAuthenticated, HasLojaAccess]

    def get(self, request, paciente_id):
        ensure_loja_context(request)
        paciente = Paciente.objects.filter(pk=paciente_id, is_active=True).first()
        if not paciente:
            return Response({"detail": "Paciente não encontrado."}, status=404)
        evolucoes = Evolucao.objects.filter(paciente=paciente).select_related("consulta")
        prescricoes = Prescricao.objects.filter(paciente=paciente).prefetch_related("itens")
        return Response(
            {
                "paciente": PacienteSerializer(paciente).data,
                "evolucoes": EvolucaoSerializer(evolucoes, many=True).data,
                "prescricoes": PrescricaoSerializer(prescricoes, many=True).data,
            }
        )
