from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import HasLojaAccess
from core.views import BaseModelViewSet
from tenants.middleware import ensure_loja_context

from .config_service import get_or_create_config
from .models import Evolucao, Prescricao
from .pdf_service import pdf_evolucao, pdf_receita, pdf_response
from .serializers import EvolucaoSerializer, PrescricaoSerializer


class EvolucaoViewSet(BaseModelViewSet):
    serializer_class = EvolucaoSerializer

    def get_queryset(self):
        ensure_loja_context(self.request)
        qs = Evolucao.objects.select_related("consulta", "paciente")
        paciente = (self.request.query_params.get("paciente") or "").strip()
        consulta = (self.request.query_params.get("consulta") or "").strip()
        if paciente:
            qs = qs.filter(paciente_id=paciente)
        if consulta:
            qs = qs.filter(consulta_id=consulta)
        return qs

    def perform_create(self, serializer):
        ensure_loja_context(self.request)
        config = get_or_create_config()
        serializer.save(especialidade=serializer.validated_data.get("especialidade") or config.especialidade)


class PrescricaoViewSet(BaseModelViewSet):
    serializer_class = PrescricaoSerializer

    def get_queryset(self):
        ensure_loja_context(self.request)
        qs = Prescricao.objects.prefetch_related("itens").select_related("paciente", "consulta")
        consulta = (self.request.query_params.get("consulta") or "").strip()
        if consulta:
            qs = qs.filter(consulta_id=consulta)
        return qs

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        ensure_loja_context(request)
        presc = self.get_object()
        return pdf_response(
            pdf_receita(presc, presc.consulta, presc.paciente, get_or_create_config()),
            f"receita-{presc.id}.pdf",
            paciente=presc.paciente,
        )


class EvolucaoPDFView(APIView):
    permission_classes = [IsAuthenticated, HasLojaAccess]

    def get(self, request, pk):
        ensure_loja_context(request)
        ev = Evolucao.objects.select_related("consulta", "paciente").filter(pk=pk).first()
        if not ev:
            return Response({"detail": "Evolução não encontrada."}, status=404)
        return pdf_response(
            pdf_evolucao(ev, ev.consulta, ev.paciente, get_or_create_config()),
            f"evolucao-{ev.id}.pdf",
            paciente=ev.paciente,
        )
