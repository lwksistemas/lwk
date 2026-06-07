"""Serializers financeiros."""
from rest_framework import serializers

from ..models import CategoriaDespesa, Despesa, Payment
from .appointments import AppointmentListSerializer


class CategoriaDespesaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaDespesa
        exclude = ['loja_id']
        read_only_fields = ['created_at']


class DespesaSerializer(serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True, default=None)

    class Meta:
        model = Despesa
        exclude = ['loja_id']
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, attrs):
        status = attrs.get('status', getattr(self.instance, 'status', None))
        data_pag = attrs.get('data_pagamento', getattr(self.instance, 'data_pagamento', None))
        if status == 'PAID' and not data_pag:
            attrs['data_pagamento'] = attrs.get('data_vencimento') or getattr(
                self.instance, 'data_vencimento', None,
            )
        return attrs


def _procedimentos_nome_agendamento(appointment) -> str:
    """Lista todos os procedimentos do atendimento (appointment_procedures ou legado)."""
    if not appointment:
        return ''
    procs = list(
        appointment.appointment_procedures.select_related('procedure').order_by('ordem', 'id'),
    )
    if procs:
        return ' · '.join(ap.procedure.nome for ap in procs if ap.procedure)
    if appointment.procedure_id and appointment.procedure:
        return appointment.procedure.nome
    return ''


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer para Pagamentos (financeiro da clínica)."""
    appointment_details = AppointmentListSerializer(source='appointment', read_only=True)
    paciente_nome = serializers.CharField(source='appointment.patient.nome', read_only=True)
    profissional_nome = serializers.CharField(source='appointment.professional.nome', read_only=True)
    procedimento_nome = serializers.SerializerMethodField()
    data_atendimento = serializers.DateTimeField(source='appointment.date', read_only=True)

    def get_procedimento_nome(self, obj):
        return _procedimentos_nome_agendamento(obj.appointment)

    class Meta:
        model = Payment
        exclude = ['loja_id']
