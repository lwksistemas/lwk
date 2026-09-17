"""Bloqueios de horário da agenda."""
import logging

from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from clinica_beleza.models import BloqueioHorario
from clinica_beleza.permissions import CLINICA_AGENDA, resolve_agenda_professional_scope
from clinica_beleza.serializers import BloqueioHorarioSerializer
from clinica_beleza.views_agenda.helpers import (
    _agenda_scope_forbidden_response,
    _apply_agenda_bloqueio_scope,
)
from clinica_beleza.views_base import GetObjectMixin

logger = logging.getLogger(__name__)


class BloqueioHorarioListView(APIView):
    """GET /clinica-beleza/bloqueios/  POST /clinica-beleza/bloqueios/"""

    permission_classes = CLINICA_AGENDA

    def get(self, request):
        qs = BloqueioHorario.objects.all().select_related("professional").order_by("-data_inicio")
        if s := request.query_params.get("start"):
            qs = qs.filter(data_fim__gte=s)
        if e := request.query_params.get("end"):
            qs = qs.filter(data_inicio__lte=e)
        scope = resolve_agenda_professional_scope(request)
        if scope is None and (p := request.query_params.get("professional")):
            qs = qs.filter(Q(professional_id=p) | Q(professional_id__isnull=True))
        else:
            qs = _apply_agenda_bloqueio_scope(qs, request)
        return Response(BloqueioHorarioSerializer(qs, many=True).data)

    def post(self, request):
        scope = resolve_agenda_professional_scope(request)
        data = dict(request.data)
        if scope is not None:
            prof_in = data.get("professional")
            if prof_in and int(prof_in) != scope:
                return _agenda_scope_forbidden_response()
            if not prof_in:
                data["professional"] = scope
        serializer = BloqueioHorarioSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception("Erro ao criar BloqueioHorario: %s", e)
            return Response(
                {"error": "Erro ao salvar bloqueio. Verifique data/hora e tente novamente."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class BloqueioHorarioDetailView(GetObjectMixin, APIView):
    """GET /clinica-beleza/bloqueios/<id>/  PUT  DELETE"""

    permission_classes = CLINICA_AGENDA
    model_class = BloqueioHorario
    not_found_message = "Bloqueio não encontrado"
    select_related_fields = ["professional"]

    def get(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        scope = resolve_agenda_professional_scope(request)
        if scope is not None and scope and obj.professional_id not in (scope, None):
            return _agenda_scope_forbidden_response()
        return Response(BloqueioHorarioSerializer(obj).data)

    def put(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        scope = resolve_agenda_professional_scope(request)
        if scope is not None and scope and obj.professional_id not in (scope, None):
            return _agenda_scope_forbidden_response()
        if scope is not None:
            prof_in = request.data.get("professional")
            if prof_in and int(prof_in) != scope:
                return _agenda_scope_forbidden_response()
        serializer = BloqueioHorarioSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        return self.put(request, pk)

    def delete(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        scope = resolve_agenda_professional_scope(request)
        if scope is not None and scope and obj.professional_id not in (scope, None):
            return _agenda_scope_forbidden_response()
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
