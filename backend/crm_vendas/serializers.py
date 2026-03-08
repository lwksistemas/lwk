from rest_framework import serializers
from .models import Vendedor, Conta, Lead, Contato, Oportunidade, Atividade


class VendedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendedor
        fields = [
            'id', 'nome', 'email', 'telefone', 'cargo', 'is_admin', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class ContaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conta
        fields = [
            'id', 'nome', 'segmento', 'telefone', 'email', 'cidade', 'endereco',
            'observacoes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = [
            'id', 'nome', 'empresa', 'email', 'telefone', 'origem', 'status',
            'valor_estimado', 'conta', 'observacoes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class LeadListSerializer(serializers.ModelSerializer):
    conta_nome = serializers.CharField(source='conta.nome', read_only=True)

    class Meta:
        model = Lead
        fields = [
            'id', 'nome', 'empresa', 'email', 'origem', 'status', 'valor_estimado',
            'conta', 'conta_nome', 'created_at',
        ]


class ContatoSerializer(serializers.ModelSerializer):
    conta_nome = serializers.CharField(source='conta.nome', read_only=True)

    class Meta:
        model = Contato
        fields = [
            'id', 'nome', 'email', 'telefone', 'cargo', 'conta', 'conta_nome',
            'observacoes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class OportunidadeSerializer(serializers.ModelSerializer):
    lead_nome = serializers.CharField(source='lead.nome', read_only=True)
    vendedor_nome = serializers.CharField(source='vendedor.nome', read_only=True)

    class Meta:
        model = Oportunidade
        fields = [
            'id', 'titulo', 'lead', 'lead_nome', 'valor', 'etapa', 'vendedor', 'vendedor_nome',
            'probabilidade', 'data_fechamento_prevista', 'data_fechamento', 'observacoes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class AtividadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Atividade
        fields = [
            'id', 'titulo', 'tipo', 'oportunidade', 'lead', 'data', 'concluido',
            'observacoes', 'google_event_id', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
