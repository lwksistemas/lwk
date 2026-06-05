"""Serializers financeiros."""
from rest_framework import serializers

from ..models import Payment
from .appointments import AppointmentListSerializer


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer para Pagamentos (financeiro da clínica)."""
    appointment_details = AppointmentListSerializer(source='appointment', read_only=True)
    paciente_nome = serializers.CharField(source='appointment.patient.nome', read_only=True)
    profissional_nome = serializers.CharField(source='appointment.professional.nome', read_only=True)
    procedimento_nome = serializers.CharField(source='appointment.procedure.nome', read_only=True)
    data_atendimento = serializers.DateTimeField(source='appointment.date', read_only=True)

    class Meta:
        model = Payment
        exclude = ['loja_id']
