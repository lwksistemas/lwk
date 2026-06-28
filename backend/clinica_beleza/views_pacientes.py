"""
Views de Pacientes — Clínica da Beleza
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import CLINICA_RECEPCAO
from rest_framework import status

from .models import Patient, Appointment
from .serializers import PatientSerializer
from .views_base import GetObjectMixin, map_field_names
from .pagination import paginate_queryset

# Status de agendamento ainda "em aberto" (não terminais)
_OPEN_APPOINTMENT_STATUSES = ('PENDING', 'SCHEDULED', 'CLIENT_CONFIRMED', 'PHONE_CONFIRMED', 'CONFIRMED', 'IN_PROGRESS')

logger = logging.getLogger(__name__)

# Mapeamento de campos inglês → português
_PATIENT_FIELD_MAP = {
    'name': 'nome',
    'phone': 'telefone',
    'birth_date': 'data_nascimento',
    'address': 'endereco',
    'notes': 'observacoes',
    'active': 'is_active',
    'photo_url': 'foto_url',
}
_PATIENT_NULL_FIELDS = ('telefone', 'endereco', 'observacoes', 'cpf', 'cidade', 'estado', 'foto_url')


def _map_patient_data(raw_data):
    """Normaliza campos inglês→português e converte None para '' em campos de texto."""
    return map_field_names(raw_data, _PATIENT_FIELD_MAP, _PATIENT_NULL_FIELDS)


def _patient_search_q(search: str):
    """Busca por prefixo do nome; telefone/CPF por dígitos (não casa 'L' dentro de 'FELIX')."""
    from django.db.models import Q

    search = (search or '').strip()
    if not search:
        return Q()
    digits = ''.join(c for c in search if c.isdigit())
    has_letters = any(c.isalpha() for c in search)
    if len(digits) >= 3 and not has_letters:
        return Q(telefone__icontains=digits) | Q(cpf__icontains=digits)
    if len(digits) >= 3:
        return (
            Q(nome__istartswith=search)
            | Q(telefone__icontains=digits)
            | Q(cpf__icontains=digits)
        )
    return Q(nome__istartswith=search)


class PatientListView(APIView):
    """
    Listagem e criação de pacientes
    GET /clinica-beleza/patients/
    POST /clinica-beleza/patients/
    """
    permission_classes = CLINICA_RECEPCAO

    def get(self, request):
        active_only = request.query_params.get('active', 'true').lower() == 'true'
        queryset = Patient.objects.select_related('convenio').order_by('nome')
        if active_only:
            queryset = queryset.filter(is_active=True)
        search = (request.query_params.get('search') or '').strip()
        if search:
            queryset = queryset.filter(_patient_search_q(search))
        return paginate_queryset(queryset, request, PatientSerializer)

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


class PatientDetailView(GetObjectMixin, APIView):
    """GET /clinica-beleza/patients/<id>/  PUT  DELETE"""
    permission_classes = CLINICA_RECEPCAO
    model_class = Patient
    not_found_message = 'Paciente não encontrado'
    select_related_fields = ('convenio',)

    def get(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        return Response(PatientSerializer(obj).data)

    def put(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        data = _map_patient_data(request.data)
        serializer = PatientSerializer(obj, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        from django.utils import timezone
        from django.db.models import F

        obj, err = self.object_or_404(pk)
        if err:
            return err
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
