from django.db.models import Q
from rest_framework import serializers
from core.serializers import BaseLojaSerializer
from .models import Hospede, Quarto, Tarifa, Reserva, GovernancaTarefa, Funcionario


class HospedeSerializer(BaseLojaSerializer):
    class Meta:
        model = Hospede
        fields = [
            'id', 'nome', 'documento', 'telefone', 'email',
            'observacoes', 'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'loja_id']


class QuartoSerializer(BaseLojaSerializer):
    class Meta:
        model = Quarto
        fields = [
            'id', 'numero', 'nome', 'tipo', 'capacidade',
            'status', 'observacoes', 'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'loja_id']


class TarifaSerializer(BaseLojaSerializer):
    class Meta:
        model = Tarifa
        fields = [
            'id', 'nome', 'tipo_quarto', 'valor_diaria',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'loja_id']


class ReservaSerializer(BaseLojaSerializer):
    hospede_nome = serializers.CharField(source='hospede.nome', read_only=True)
    quarto_numero = serializers.CharField(source='quarto.numero', read_only=True)
    quarto_nome = serializers.CharField(source='quarto.nome', read_only=True)
    tarifa_nome = serializers.CharField(source='tarifa.nome', read_only=True, allow_null=True)

    class Meta:
        model = Reserva
        fields = [
            'id', 'hospede', 'hospede_nome', 'quarto', 'quarto_numero', 'quarto_nome',
            'tarifa', 'tarifa_nome', 'data_checkin', 'data_checkout',
            'adultos', 'criancas', 'canal', 'status',
            'valor_diaria', 'valor_total', 'observacoes',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'loja_id']

    def validate(self, data):
        data_checkin = data.get('data_checkin') or getattr(self.instance, 'data_checkin', None)
        data_checkout = data.get('data_checkout') or getattr(self.instance, 'data_checkout', None)
        if data_checkin and data_checkout and data_checkout <= data_checkin:
            raise serializers.ValidationError({'data_checkout': 'Checkout deve ser após o check-in.'})

        # Validar conflito de datas no mesmo quarto
        quarto = data.get('quarto') or getattr(self.instance, 'quarto', None)
        if quarto and data_checkin and data_checkout:
            conflito_qs = Reserva.objects.filter(
                quarto=quarto,
                is_active=True,
                data_checkin__lt=data_checkout,
                data_checkout__gt=data_checkin,
            ).exclude(
                status__in=[Reserva.STATUS_CANCELADA, Reserva.STATUS_NO_SHOW],
            )
            if self.instance:
                conflito_qs = conflito_qs.exclude(pk=self.instance.pk)
            if conflito_qs.exists():
                raise serializers.ValidationError({
                    'quarto': 'Este quarto já possui reserva ativa neste período.',
                })

        return data


class GovernancaTarefaSerializer(BaseLojaSerializer):
    quarto_numero = serializers.CharField(source='quarto.numero', read_only=True)

    class Meta:
        model = GovernancaTarefa
        fields = [
            'id', 'quarto', 'quarto_numero', 'tipo', 'status',
            'descricao', 'prioridade', 'concluido_em',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'concluido_em', 'loja_id']


class FuncionarioSerializer(BaseLojaSerializer):
    class Meta:
        model = Funcionario
        fields = [
            'id', 'nome', 'email', 'cargo', 'telefone',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'loja_id']
