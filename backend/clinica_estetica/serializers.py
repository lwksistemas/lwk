from rest_framework import serializers
from core.serializers import BaseLojaSerializer
from .models import (
    Cliente, Profissional, Procedimento, Agendamento, Funcionario,
    ProtocoloProcedimento, EvolucaoPaciente, AnamnesesTemplate, Anamnese,
    HorarioFuncionamento, BloqueioAgenda, Consulta
)


class ClienteSerializer(BaseLojaSerializer):
    """
    Serializer de Cliente.
    Herda de BaseLojaSerializer para adicionar loja_id automaticamente.
    """

    total_agendamentos = serializers.SerializerMethodField()
    ultima_visita = serializers.SerializerMethodField()

    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']

    def get_total_agendamentos(self, obj):
        return obj.agendamentos.count()

    def get_ultima_visita(self, obj):
        ultimo = obj.agendamentos.filter(status='concluido').order_by('-data').first()
        return ultimo.data if ultimo else None


class ProfissionalSerializer(BaseLojaSerializer):
    """Serializer de Profissional."""

    total_agendamentos = serializers.SerializerMethodField()

    class Meta:
        model = Profissional
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']

    def get_total_agendamentos(self, obj):
        return obj.agendamentos.count()


class ProcedimentoSerializer(BaseLojaSerializer):
    """Serializer de Procedimento."""

    total_protocolos = serializers.SerializerMethodField()

    class Meta:
        model = Procedimento
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']

    def get_total_protocolos(self, obj):
        return obj.protocolos.filter(is_active=True).count()


class ProtocoloProcedimentoSerializer(BaseLojaSerializer):
    procedimento_nome = serializers.CharField(source='procedimento.nome', read_only=True)

    class Meta:
        model = ProtocoloProcedimento
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']


class AgendamentoSerializer(BaseLojaSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    cliente_telefone = serializers.CharField(source='cliente.telefone', read_only=True)
    profissional_nome = serializers.CharField(source='profissional.nome', read_only=True)
    procedimento_nome = serializers.CharField(source='procedimento.nome', read_only=True)
    procedimento_duracao = serializers.IntegerField(source='procedimento.duracao', read_only=True)

    class Meta:
        model = Agendamento
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']

    def create(self, validated_data):
        """Cria agendamento e consulta associada."""
        # BaseLojaSerializer já adiciona loja_id
        agendamento = super().create(validated_data)

        # Criar Consulta com status 'agendada' para aparecer no Sistema de Consultas
        Consulta.objects.get_or_create(
            agendamento=agendamento,
            defaults={
                'cliente_id': agendamento.cliente_id,
                'profissional_id': agendamento.profissional_id,
                'procedimento_id': agendamento.procedimento_id,
                'status': 'agendada',
                'valor_consulta': agendamento.valor,
                'loja_id': agendamento.loja_id,
            }
        )
        return agendamento

        # Criar Consulta com status 'agendada' para aparecer no Sistema de Consultas
        Consulta.objects.get_or_create(
            agendamento=agendamento,
            defaults={
                'cliente_id': agendamento.cliente_id,
                'profissional_id': agendamento.profissional_id,
                'procedimento_id': agendamento.procedimento_id,
                'status': 'agendada',
                'valor_consulta': agendamento.valor,
                'loja_id': agendamento.loja_id,
            }
        )
        return agendamento


class EvolucaoPacienteSerializer(BaseLojaSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    profissional_nome = serializers.CharField(source='profissional.nome', read_only=True)
    agendamento_info = serializers.SerializerMethodField()
    imc = serializers.ReadOnlyField()

    class Meta:
        model = EvolucaoPaciente
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'data_evolucao', 'loja_id']

    def get_agendamento_info(self, obj):
        if obj.agendamento:
            return {
                'procedimento': obj.agendamento.procedimento.nome,
                'data': obj.agendamento.data,
                'horario': obj.agendamento.horario
            }
        return None


class AnamnesesTemplateSerializer(serializers.ModelSerializer):
    procedimento_nome = serializers.CharField(source='procedimento.nome', read_only=True)
    total_perguntas = serializers.SerializerMethodField()

    class Meta:
        model = AnamnesesTemplate
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_total_perguntas(self, obj):
        return len(obj.perguntas) if obj.perguntas else 0


class AnamneseSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    template_nome = serializers.CharField(source='template.nome', read_only=True)
    agendamento_info = serializers.SerializerMethodField()

    class Meta:
        model = Anamnese
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_agendamento_info(self, obj):
        if obj.agendamento:
            return {
                'procedimento': obj.agendamento.procedimento.nome,
                'data': obj.agendamento.data,
                'horario': obj.agendamento.horario
            }
        return None


class HorarioFuncionamentoSerializer(serializers.ModelSerializer):
    dia_semana_nome = serializers.CharField(source='get_dia_semana_display', read_only=True)

    class Meta:
        model = HorarioFuncionamento
        fields = '__all__'


class BloqueioAgendaSerializer(serializers.ModelSerializer):
    tipo_nome = serializers.CharField(source='get_tipo_display', read_only=True)
    profissional_nome = serializers.CharField(source='profissional.nome', read_only=True)

    class Meta:
        model = BloqueioAgenda
        fields = '__all__'
        read_only_fields = ['created_at']


class FuncionarioSerializer(BaseLojaSerializer):
    class Meta:
        model = Funcionario
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']


# Serializers para busca de clientes
class ClienteBuscaSerializer(serializers.ModelSerializer):
    """Serializer simplificado para busca de clientes"""
    class Meta:
        model = Cliente
        fields = ['id', 'nome', 'telefone', 'email']


class ConsultaSerializer(serializers.ModelSerializer):
    """Serializer para consultas"""
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    profissional_nome = serializers.CharField(source='profissional.nome', read_only=True)
    procedimento_nome = serializers.CharField(source='procedimento.nome', read_only=True)
    agendamento_data = serializers.DateField(source='agendamento.data', read_only=True)
    agendamento_horario = serializers.TimeField(source='agendamento.horario', read_only=True)
    duracao_minutos = serializers.ReadOnlyField()
    total_evolucoes = serializers.SerializerMethodField()

    class Meta:
        model = Consulta
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_total_evolucoes(self, obj):
        return obj.evolucoes.count()
