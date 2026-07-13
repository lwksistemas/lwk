"""Procedimentos do atendimento — adicionar/remover durante a consulta."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..consulta_procedimentos_service import (
    adicionar_procedimento_consulta,
    remover_procedimento_consulta,
)
from ..models import Consulta
from ..permissions import CLINICA_CLINICAL
from ..serializers import AppointmentProcedureSerializer, ConsultaSerializer


class ConsultaProcedimentoListView(APIView):
    """GET  /clinica-beleza/consultas/<consulta_id>/procedimentos/
    POST /clinica-beleza/consultas/<consulta_id>/procedimentos/
    """

    permission_classes = CLINICA_CLINICAL

    def _get_consulta(self, consulta_id):
        try:
            return (
                Consulta.objects.select_related("appointment")
                .prefetch_related("appointment__appointment_procedures__procedure")
                .get(pk=consulta_id),
                None,
            )
        except Consulta.DoesNotExist:
            return None, Response({"error": "Consulta não encontrada"}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request, consulta_id):
        consulta, error = self._get_consulta(consulta_id)
        if error:
            return error
        from ..consulta_procedimentos_service import _garantir_procedimentos_legacy

        _garantir_procedimentos_legacy(consulta.appointment)
        qs = consulta.appointment.appointment_procedures.select_related("procedure").order_by("ordem", "id")
        return Response(AppointmentProcedureSerializer(qs, many=True).data)

    def post(self, request, consulta_id):
        consulta, error = self._get_consulta(consulta_id)
        if error:
            return error

        procedure_id = request.data.get("procedure")
        if not procedure_id:
            return Response({"error": "Informe o procedimento."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ap = adicionar_procedimento_consulta(consulta, int(procedure_id))
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        ap = consulta.appointment.appointment_procedures.select_related("procedure").get(pk=ap.pk)
        consulta.refresh_from_db()
        return Response(
            {
                "item": AppointmentProcedureSerializer(ap).data,
                "consulta": ConsultaSerializer(consulta).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ConsultaProcedimentoDetailView(APIView):
    """DELETE /clinica-beleza/consultas/<consulta_id>/procedimentos/<pk>/"""

    permission_classes = CLINICA_CLINICAL

    def delete(self, request, consulta_id, pk):
        try:
            consulta = Consulta.objects.select_related("appointment").get(pk=consulta_id)
        except Consulta.DoesNotExist:
            return Response({"error": "Consulta não encontrada"}, status=status.HTTP_404_NOT_FOUND)

        try:
            remover_procedimento_consulta(consulta, int(pk))
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        consulta.refresh_from_db()
        return Response({"consulta": ConsultaSerializer(consulta).data}, status=status.HTTP_200_OK)
