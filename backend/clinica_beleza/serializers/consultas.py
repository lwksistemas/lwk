"""Serializers de consultas, evoluções e prescrições Memed."""
from decimal import Decimal

from rest_framework import serializers

from ..models import Consulta, ConsultaEvolucao, Convenio, LocalAtendimento, PrescricaoMemed


class ConsultaEvolucaoSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.nome', read_only=True)
    professional_name = serializers.CharField(source='professional.nome', read_only=True, default=None)

    class Meta:
        model = ConsultaEvolucao
        fields = [
            'id', 'consulta', 'patient', 'patient_name', 'professional', 'professional_name',
            'descricao', 'procedimento_realizado', 'produtos_utilizados', 'orientacoes',
            'protocolo_snapshot', 'satisfacao', 'created_at', 'updated_at', 'loja_id',
        ]
        read_only_fields = ['created_at', 'updated_at', 'loja_id']


class PrescricaoMemedSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.nome', read_only=True)
    professional_name = serializers.CharField(source='professional.nome', read_only=True, default=None)

    class Meta:
        model = PrescricaoMemed
        fields = [
            'id', 'consulta', 'patient', 'patient_name', 'professional', 'professional_name',
            'prescricao_id', 'resumo', 'itens', 'pdf_url', 'created_at', 'loja_id',
        ]
        read_only_fields = ['created_at', 'loja_id']


class ConsultaSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.nome', read_only=True)
    professional_name = serializers.CharField(source='professional.nome', read_only=True, default=None)
    procedure_name = serializers.SerializerMethodField()
    procedures_list = serializers.SerializerMethodField()
    protocol_name = serializers.CharField(source='protocol.nome', read_only=True, default=None)
    appointment_date = serializers.DateTimeField(source='appointment.date', read_only=True)
    appointment_status = serializers.CharField(source='appointment.status', read_only=True)
    duracao_minutos = serializers.ReadOnlyField()
    total_evolucoes = serializers.SerializerMethodField()
    local_atendimento = serializers.PrimaryKeyRelatedField(
        queryset=LocalAtendimento.objects.all(),
        allow_null=True,
        required=False,
    )
    local_atendimento_name = serializers.CharField(
        source='local_atendimento.nome', read_only=True, default=None, allow_null=True,
    )
    convenio = serializers.PrimaryKeyRelatedField(
        queryset=Convenio.objects.filter(is_active=True),
        allow_null=True,
        required=False,
    )
    convenio_name = serializers.SerializerMethodField()
    valor_procedimentos = serializers.SerializerMethodField()
    valor_pagamento = serializers.SerializerMethodField()

    class Meta:
        model = Consulta
        fields = [
            'id', 'appointment', 'patient', 'patient_name', 'professional', 'professional_name',
            'procedure', 'procedure_name', 'procedures_list', 'protocol', 'protocol_name', 'status',
            'data_inicio', 'data_fim', 'duracao_minutos', 'observacoes_gerais', 'protocolo_notas',
            'valor_consulta', 'valor_procedimentos', 'valor_pagamento',
            'local_atendimento', 'local_atendimento_name',
            'convenio', 'convenio_name',
            'appointment_date', 'appointment_status', 'total_evolucoes',
            'created_at', 'updated_at', 'loja_id',
        ]
        read_only_fields = ['created_at', 'updated_at', 'loja_id', 'appointment']

    def get_total_evolucoes(self, obj):
        return obj.evolucoes.count()

    def _appointment_procedures(self, obj):
        appointment = getattr(obj, 'appointment', None)
        if not appointment:
            return []
        return list(
            appointment.appointment_procedures.select_related('procedure').order_by('ordem', 'id'),
        )

    def get_procedure_name(self, obj):
        procs = self._appointment_procedures(obj)
        if procs:
            return ', '.join(ap.procedure.nome for ap in procs)
        if obj.procedure_id and obj.procedure:
            return obj.procedure.nome
        return ''

    def get_procedures_list(self, obj):
        procs = self._appointment_procedures(obj)
        if procs:
            return [
                {
                    'id': ap.procedure_id,
                    'nome': ap.procedure.nome,
                    'valor': float(ap.get_valor()),
                }
                for ap in procs
            ]
        if obj.procedure_id and obj.procedure:
            return [{
                'id': obj.procedure_id,
                'nome': obj.procedure.nome,
                'valor': float(obj.procedure.preco or 0),
            }]
        return []

    def _appointment_valor_procedimentos(self, obj) -> Decimal:
        appointment = getattr(obj, 'appointment', None)
        if not appointment:
            return Decimal('0')
        return Decimal(str(appointment.valor_total or 0))

    def get_valor_procedimentos(self, obj):
        return float(self._appointment_valor_procedimentos(obj))

    def get_valor_pagamento(self, obj):
        vc = Decimal(str(obj.valor_consulta or 0))
        return float(vc + self._appointment_valor_procedimentos(obj))

    def get_convenio_name(self, obj):
        if obj.convenio_id and obj.convenio:
            return obj.convenio.nome
        return 'Particular'
