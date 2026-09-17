"""Detalhe, edição e exclusão de consulta."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..consulta_service import consulta_esta_concluida, motivo_bloqueio_exclusao_consulta
from ..models import Consulta
from ..permissions import CLINICA_CLINICAL
from ..serializers import ConsultaSerializer
from ..views_base import GetObjectMixin


class ConsultaDetailView(GetObjectMixin, APIView):
    """GET / PUT / PATCH /clinica-beleza/consultas/<id>/"""

    permission_classes = CLINICA_CLINICAL
    model_class = Consulta
    not_found_message = "Consulta não encontrada"
    select_related_fields = (
        "patient", "professional", "procedure", "protocol", "appointment",
        "appointment__nome_agenda", "local_atendimento", "convenio",
    )
    prefetch_related_fields = (
        "appointment__appointment_procedures__procedure",
        "appointment__payment_set",
    )

    def get(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        return Response(ConsultaSerializer(obj).data)

    def put(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        if consulta_esta_concluida(obj):
            campos_permitidos = {"convenio", "local_atendimento"}
            campos_enviados = set(request.data.keys())
            if not campos_enviados.issubset(campos_permitidos):
                return Response(
                    {"error": "Consulta finalizada — só é possível editar convênio e local de atendimento."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        serializer = ConsultaSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        return self.put(request, pk)

    def delete(self, request, pk):
        consulta, err = self.object_or_404(pk)
        if err:
            return err

        if motivo := motivo_bloqueio_exclusao_consulta(consulta):
            return Response({"error": motivo}, status=status.HTTP_403_FORBIDDEN)

        appointment = consulta.appointment
        if appointment and appointment.status not in ("COMPLETED", "CANCELLED"):
            appointment.status = "CANCELLED"
            appointment.version = (appointment.version or 1) + 1
            appointment.save(update_fields=["status", "version", "updated_at"])

        from ..foto_paciente_service import limpar_fotos_media_da_consulta

        limpar_fotos_media_da_consulta(consulta)

        consulta.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
