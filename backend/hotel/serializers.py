from rest_framework import serializers
from core.serializers import BaseLojaSerializer
from .models import Hospede, Quarto, Tarifa, Reserva, GovernancaTarefa


class HospedeSerializer(BaseLojaSerializer):
    class Meta:
        model = Hospede
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']


class QuartoSerializer(BaseLojaSerializer):
    class Meta:
        model = Quarto
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']


class TarifaSerializer(BaseLojaSerializer):
    class Meta:
        model = Tarifa
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']


class ReservaSerializer(BaseLojaSerializer):
    hospede_nome = serializers.CharField(source='hospede.nome', read_only=True)
    quarto_numero = serializers.CharField(source='quarto.numero', read_only=True)
    quarto_nome = serializers.CharField(source='quarto.nome', read_only=True)
    tarifa_nome = serializers.CharField(source='tarifa.nome', read_only=True, allow_null=True)

    class Meta:
        model = Reserva
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']

    def validate(self, data):
        data_checkin = data.get('data_checkin') or getattr(self.instance, 'data_checkin', None)
        data_checkout = data.get('data_checkout') or getattr(self.instance, 'data_checkout', None)
        if data_checkin and data_checkout and data_checkout <= data_checkin:
            raise serializers.ValidationError({'data_checkout': 'Checkout deve ser após o check-in.'})
        return data


class GovernancaTarefaSerializer(BaseLojaSerializer):
    quarto_numero = serializers.CharField(source='quarto.numero', read_only=True)

    class Meta:
        model = GovernancaTarefa
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'concluido_em', 'loja_id']

