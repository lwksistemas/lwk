"""
Views de Pacientes — Clínica da Beleza
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Patient, Appointment
from .serializers import PatientSerializer

# Status de agendamento ainda "em aberto" (não terminais)
_OPEN_APPOINTMENT_STATUSES = ('PENDING', 'SCHEDULED', 'CONFIRMED', 'IN_PROGRESS')

logger = logging.getLogger(__name__)

# Mapeamento de campos inglês → português (reutilizado em list e detail)
_PATIENT_FIELD_MAP = {
    'name': 'nome',
    'phone': 'telefone',
    'birth_date': 'data_nascimento',
    'address': 'endereco',
    'notes': 'observacoes',
    'active': 'is_active',
}
_PATIENT_NULL_FIELDS = ('telefone', 'endereco', 'observacoes', 'cpf', 'cidade', 'estado')


def _map_patient_data(raw_data):
    """Normaliza campos inglês→português e converte None para '' em campos de texto."""
    data = raw_data.copy() if hasattr(raw_data, 'copy') else dict(raw_data)
    for en, pt in _PATIENT_FIELD_MAP.items():
        if en in data and pt not in data:
            data[pt] = data.pop(en)
    for field in _PATIENT_NULL_FIELDS:
        if field in data and data[field] is None:
            data[field] = ''
    return data


class PatientListView(APIView):
    """
    Listagem e criação de pacientes
    GET /clinica-beleza/patients/
    POST /clinica-beleza/patients/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_only = request.query_params.get('active', 'true').lower() == 'true'
        queryset = Patient.objects.all().order_by('nome')
        if active_only:
            queryset = queryset.filter(is_active=True)
        return Response(PatientSerializer(queryset, many=True).data)

    def post(self, request):
        data = _map_patient_data(request.data)
        serializer = PatientSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning(
            'Erro ao criar paciente: erros=%s, campos=%s',
            serializer.errors, sorted(data.keys()),
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PatientDetailView(APIView):
    """GET /clinica-beleza/patients/<id>/  PUT  DELETE"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            return Response(PatientSerializer(Patient.objects.get(pk=pk)).data)
        except Patient.DoesNotExist:
            return Response({'error': 'Paciente não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            obj = Patient.objects.get(pk=pk)
            data = _map_patient_data(request.data)
            serializer = PatientSerializer(obj, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Patient.DoesNotExist:
            return Response({'error': 'Paciente não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            from django.utils import timezone
            from django.db.models import F

            obj = Patient.objects.get(pk=pk)
            agora = timezone.now()
            # Cancela os agendamentos futuros em aberto, liberando os horários.
            # O histórico (concluídos/cancelados/faltas) é preservado.
            canceladas = Appointment.objects.filter(
                patient=obj,
                date__gte=agora,
                status__in=_OPEN_APPOINTMENT_STATUSES,
            ).update(status='CANCELLED', updated_at=agora, version=F('version') + 1)
            obj.is_active = False
            obj.save()
            return Response(
                {'message': f'Paciente desativado. {canceladas} agendamento(s) futuro(s) cancelado(s).'},
                status=status.HTTP_200_OK,
            )
        except Patient.DoesNotExist:
            return Response({'error': 'Paciente não encontrado'}, status=status.HTTP_404_NOT_FOUND)
