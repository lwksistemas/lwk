"""Serializers de agendamentos, agenda e bloqueios."""
from rest_framework import serializers

from core.serializer_mixins import TenantQuerysetMixin
from ..bloqueio_utils import bloqueio_datetime_range, split_datetime_range
from ..models import (
    Appointment, AppointmentProcedure, BloqueioHorario, Convenio, NomeAgenda, Procedure,
)
from .patients import PatientSerializer
from .procedures import ProcedureSerializer
from .professionals import ProfessionalSerializer


class AppointmentListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de agendamentos."""
    patient_name = serializers.CharField(source='patient.nome', read_only=True)
    professional_name = serializers.CharField(source='professional.nome', read_only=True)
    procedure_name = serializers.CharField(source='procedure.nome', read_only=True)
    procedure_price = serializers.DecimalField(
        source='procedure.preco', max_digits=10, decimal_places=2, read_only=True,
    )
    time = serializers.SerializerMethodField()

    def get_time(self, obj):
        from django.utils import timezone
        local_dt = timezone.localtime(obj.date)
        return local_dt.strftime('%H:%M')

    class Meta:
        model = Appointment
        fields = [
            'id', 'date', 'time', 'status',
            'patient', 'patient_name',
            'professional', 'professional_name',
            'procedure', 'procedure_name', 'procedure_price',
            'notes', 'created_at', 'updated_at',
        ]


class AppointmentDetailSerializer(serializers.ModelSerializer):
    """Serializer detalhado para agendamentos."""
    patient = PatientSerializer(read_only=True)
    professional = ProfessionalSerializer(read_only=True)
    procedure = ProcedureSerializer(read_only=True)

    class Meta:
        model = Appointment
        exclude = ['loja_id']


class AppointmentCreateSerializer(TenantQuerysetMixin, serializers.ModelSerializer):
    """Serializer para criação de agendamentos (suporta múltiplos procedimentos)."""
    procedures_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
        help_text="Lista de IDs de procedimentos. Se enviado, substitui o campo 'procedure'.",
    )
    convenio = serializers.PrimaryKeyRelatedField(
        queryset=Convenio.objects.none(),
        required=False,
        allow_null=True,
    )
    nome_agenda = serializers.PrimaryKeyRelatedField(
        queryset=NomeAgenda.objects.none(),
        required=False,
        allow_null=True,
    )

    def apply_tenant_querysets(self):
        self.bind_tenant_queryset('convenio', Convenio.objects.filter(is_active=True))
        self.bind_tenant_queryset('nome_agenda', NomeAgenda.objects.filter(is_active=True))

    class Meta:
        model = Appointment
        fields = [
            'date', 'status', 'patient', 'professional', 'procedure',
            'procedures_ids', 'notes', 'convenio', 'nome_agenda',
        ]
        extra_kwargs = {
            'procedure': {'required': False, 'allow_null': True},
        }

    def validate(self, attrs):
        procedures_ids = attrs.pop('procedures_ids', None)
        procedure = attrs.get('procedure')
        if not procedures_ids and not procedure:
            raise serializers.ValidationError({'procedure': 'Informe pelo menos um procedimento.'})
        if procedures_ids:
            procedures = list(Procedure.objects.filter(id__in=procedures_ids, is_active=True))
            if len(procedures) != len(procedures_ids):
                raise serializers.ValidationError({'procedures_ids': 'Um ou mais procedimentos não encontrados.'})
            attrs['_procedures_list'] = procedures
            if not procedure:
                attrs['procedure'] = procedures[0]
        convenio = attrs.get('convenio')
        if convenio is None and attrs.get('patient'):
            patient = attrs['patient']
            if getattr(patient, 'convenio_id', None) and patient.convenio and patient.convenio.is_active:
                attrs['convenio'] = patient.convenio
        return attrs

    def create(self, validated_data):
        from ..convenio_service import criar_appointment_procedures

        procedures_list = validated_data.pop('_procedures_list', None)
        convenio = validated_data.get('convenio')
        appointment = super().create(validated_data)
        if procedures_list:
            criar_appointment_procedures(appointment, procedures_list, convenio=convenio)
        elif appointment.procedure_id:
            criar_appointment_procedures(appointment, [appointment.procedure], convenio=convenio)
        return appointment


class AppointmentProcedureSerializer(serializers.ModelSerializer):
    """Serializer para procedimentos de um agendamento."""
    procedure_name = serializers.CharField(source='procedure.nome', read_only=True)
    duracao = serializers.SerializerMethodField()
    valor_efetivo = serializers.SerializerMethodField()

    class Meta:
        model = AppointmentProcedure
        fields = [
            'id', 'procedure', 'procedure_name', 'duracao_minutos',
            'duracao', 'valor', 'valor_efetivo', 'ordem',
        ]

    def get_duracao(self, obj):
        return obj.get_duracao()

    def get_valor_efetivo(self, obj):
        return float(obj.get_valor())


class AgendaEventSerializer(serializers.ModelSerializer):
    """Serializer para eventos da agenda (formato FullCalendar)."""
    title = serializers.SerializerMethodField()
    start = serializers.DateTimeField(source='date')
    end = serializers.SerializerMethodField()
    backgroundColor = serializers.SerializerMethodField()
    borderColor = serializers.SerializerMethodField()
    textColor = serializers.SerializerMethodField()

    patient_name = serializers.CharField(source='patient.nome', read_only=True)
    patient_phone = serializers.CharField(source='patient.telefone', read_only=True)
    professional_name = serializers.CharField(source='professional.nome', read_only=True)
    professional_id = serializers.IntegerField(source='professional.id', read_only=True)
    procedure_name = serializers.SerializerMethodField()
    procedure_duration = serializers.SerializerMethodField()
    duracao_minutos = serializers.SerializerMethodField()
    procedure_price = serializers.SerializerMethodField()
    procedures_list = serializers.SerializerMethodField()
    convenio_id = serializers.IntegerField(source='convenio.id', read_only=True, allow_null=True)
    convenio_name = serializers.SerializerMethodField()
    nome_agenda_id = serializers.IntegerField(source='nome_agenda.id', read_only=True, allow_null=True)
    nome_agenda_name = serializers.CharField(source='nome_agenda.nome', read_only=True, allow_null=True, default=None)

    version = serializers.IntegerField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'title', 'start', 'end',
            'backgroundColor', 'borderColor', 'textColor',
            'status', 'notes',
            'patient', 'patient_name', 'patient_phone',
            'professional', 'professional_name', 'professional_id',
            'procedure', 'procedure_name', 'procedure_duration', 'duracao_minutos',
            'procedure_price', 'procedures_list',
            'convenio', 'convenio_id', 'convenio_name',
            'nome_agenda', 'nome_agenda_id', 'nome_agenda_name',
            'version', 'updated_at', 'updated_by_id',
        ]

    def get_title(self, obj):
        procs = obj.appointment_procedures.select_related('procedure').all()
        if procs:
            nomes = ', '.join(ap.procedure.nome for ap in procs)
            return f"{obj.patient.nome} - {nomes}"
        if obj.procedure_id:
            return f"{obj.patient.nome} - {obj.procedure.nome}"
        return obj.patient.nome

    def get_procedure_name(self, obj):
        procs = obj.appointment_procedures.select_related('procedure').all()
        if procs:
            return ', '.join(ap.procedure.nome for ap in procs)
        return obj.procedure.nome if obj.procedure_id else None

    def get_procedure_duration(self, obj):
        return obj.get_duracao_efetiva()

    def get_duracao_minutos(self, obj):
        return obj.get_duracao_efetiva()

    def get_procedure_price(self, obj):
        return float(obj.valor_total)

    def get_convenio_name(self, obj):
        if obj.convenio_id and obj.convenio:
            return obj.convenio.nome
        return 'Particular'

    def get_procedures_list(self, obj):
        procs = obj.appointment_procedures.select_related('procedure').all()
        if not procs:
            if obj.procedure_id:
                return [{
                    'id': obj.procedure_id,
                    'nome': obj.procedure.nome,
                    'duracao': obj.procedure.duracao_minutos,
                    'valor': float(obj.procedure.preco or 0),
                }]
            return []
        return [
            {
                'id': ap.procedure_id,
                'nome': ap.procedure.nome,
                'duracao': ap.get_duracao(),
                'valor': float(ap.get_valor()),
            }
            for ap in procs
        ]

    def get_end(self, obj):
        from datetime import timedelta
        return obj.date + timedelta(minutes=obj.get_duracao_efetiva())

    def get_backgroundColor(self, obj):
        colors = {
            'CONFIRMED': '#10b981',
            'PENDING': '#f59e0b',
            'SCHEDULED': '#3b82f6',
            'IN_PROGRESS': '#8b5cf6',
            'COMPLETED': '#6b7280',
            'CANCELLED': '#ef4444',
            'NO_SHOW': '#dc2626',
        }
        return colors.get(obj.status, '#3b82f6')

    def get_borderColor(self, obj):
        return self.get_backgroundColor(obj)

    def get_textColor(self, obj):
        return '#ffffff'


class BloqueioHorarioSerializer(serializers.ModelSerializer):
    """Serializer para Bloqueio de Horário (API usa datetime ISO; model usa date + time)."""
    professional_name = serializers.CharField(source='professional.nome', read_only=True, default=None)
    data_inicio = serializers.DateTimeField()
    data_fim = serializers.DateTimeField()

    class Meta:
        model = BloqueioHorario
        fields = [
            'id', 'professional', 'professional_name',
            'data_inicio', 'data_fim', 'motivo', 'observacoes', 'criado_em',
        ]
        read_only_fields = ['criado_em']

    def to_representation(self, instance):
        inicio, fim = bloqueio_datetime_range(instance)
        prof = instance.professional
        return {
            'id': instance.id,
            'professional': instance.professional_id,
            'professional_name': prof.nome if prof else None,
            'data_inicio': inicio.isoformat(),
            'data_fim': fim.isoformat(),
            'motivo': instance.motivo,
            'observacoes': instance.observacoes,
            'criado_em': instance.criado_em,
        }

    def validate(self, attrs):
        inicio = attrs.get('data_inicio')
        fim = attrs.get('data_fim')
        if inicio and fim and fim <= inicio:
            raise serializers.ValidationError({'data_fim': 'O fim deve ser depois do início.'})
        return attrs

    def create(self, validated_data):
        start = validated_data.pop('data_inicio')
        end = validated_data.pop('data_fim')
        parts = split_datetime_range(start, end)
        motivo = (validated_data.get('motivo') or '').strip() or 'Bloqueio'
        return BloqueioHorario.objects.create(
            **validated_data,
            **parts,
            titulo=motivo,
            tipo='outros',
        )

    def update(self, instance, validated_data):
        start = validated_data.pop('data_inicio', None)
        end = validated_data.pop('data_fim', None)
        if start is not None and end is not None:
            for k, v in split_datetime_range(start, end).items():
                setattr(instance, k, v)
        motivo = validated_data.get('motivo')
        if motivo is not None:
            instance.titulo = motivo
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        return instance
