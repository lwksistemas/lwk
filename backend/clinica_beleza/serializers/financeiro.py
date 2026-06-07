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
