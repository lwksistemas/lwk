from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import HasLojaAccess
from core.views import BaseModelViewSet
from tenants.middleware import ensure_loja_context

from .agenda_service import parse_iso_date, parse_periodo
from .faturamento_service import (
    consultas_atendimentos,
    consultas_periodo,
    fechar_caixa,
    pacientes_ativos,
    preview_caixa,
    relatorio_financeiro,
    relatorio_indicacao,
    relatorio_outros,
    relatorio_status,
)
from .models import FechamentoCaixa
from .serializers import ConsultaSerializer, FechamentoCaixaSerializer


class RelatoriosView(APIView):
    permission_classes = [IsAuthenticated, HasLojaAccess]

    def get(self, request):
        ensure_loja_context(request)
        tipo = (request.query_params.get("tipo") or "atendimentos").strip()
        de, ate = parse_periodo(request.query_params.get("de") or "", request.query_params.get("ate") or "")
        consultas = consultas_periodo(de, ate)
        pacientes = pacientes_ativos()
        periodo = {"de": de.isoformat(), "ate": ate.isoformat()}

        if tipo == "indicacao":
            return Response({**periodo, **relatorio_indicacao(pacientes)})
        if tipo == "status":
            return Response({**periodo, **relatorio_status(consultas)})
        if tipo == "financeiro":
            return Response({**periodo, **relatorio_financeiro(consultas)})
        if tipo == "outros":
            return Response({**periodo, **relatorio_outros(consultas, pacientes, de, ate)})

        itens = consultas_atendimentos(consultas)
        return Response(
            {
                **periodo,
                "total": consultas.exclude(status="desmarcado").count(),
                "itens": ConsultaSerializer(itens, many=True).data,
            }
        )


class FechamentoCaixaViewSet(BaseModelViewSet):
    serializer_class = FechamentoCaixaSerializer

    def get_queryset(self):
        ensure_loja_context(self.request)
        qs = FechamentoCaixa.objects.all()
        data = (self.request.query_params.get("data") or "").strip()
        if data:
            qs = qs.filter(data=data)
        return qs

    @action(detail=False, methods=["get", "post"], url_path="dia")
    def dia(self, request):
        ensure_loja_context(request)
        raw = request.query_params.get("data") or request.data.get("data") or ""
        dia = parse_iso_date(raw)
        if request.method == "POST":
            fech = fechar_caixa(dia, request.data.get("observacoes") or "")
            return Response(FechamentoCaixaSerializer(fech).data)
        return Response(preview_caixa(dia))
