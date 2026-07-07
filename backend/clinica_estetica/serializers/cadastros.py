"""Serializers de cadastros: Cliente, Profissional, Procedimento, etc."""
from rest_framework import serializers

from core.serializers import BaseLojaSerializer
from core.serializer_mixins import (
    CpfNormalizationMixin,
    TextNormalizationMixin,
    UniqueDocumentoPerLojaMixin,
)
from ..models import (
    Cliente, Profissional, Procedimento, Funcionario,
    ProtocoloProcedimento, EvolucaoPaciente, AnamnesesTemplate, Anamnese,
    HorarioFuncionamento, HorarioTrabalhoProfissional, HistoricoLogin,
)


class ClienteSerializer(
    UniqueDocumentoPerLojaMixin,
    CpfNormalizationMixin,
    TextNormalizationMixin,
    BaseLojaSerializer,
):
    """
    Serializer de Cliente.
    Herda de BaseLojaSerializer para adicionar loja_id automaticamente.
    """

    unique_documento_fields = ['cpf']
    unique_documento_entidade = 'cliente'
    unique_documento_apenas_ativos = True

    total_agendamentos = serializers.SerializerMethodField()
    ultima_visita = serializers.SerializerMethodField()
    uppercase_fields = ['nome', 'cidade', 'estado', 'bairro']
    phone_fields = ['telefone']

    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']

    def get_total_agendamentos(self, obj):
        return obj.agendamentos.count()

    def get_ultima_visita(self, obj):
        ultimo = obj.agendamentos.filter(status='concluido').order_by('-data').first()
        return ultimo.data if ultimo else None


class ClienteBuscaSerializer(serializers.ModelSerializer):
    """Serializer simplificado para busca de clientes"""
    class Meta:
        model = Cliente
        fields = ['id', 'nome', 'telefone', 'email']


class HorarioTrabalhoProfissionalSerializer(serializers.ModelSerializer):
    """Dias e horários de atendimento do profissional."""
    dia_semana_display = serializers.CharField(source='get_dia_semana_display', read_only=True)

    class Meta:
        model = HorarioTrabalhoProfissional
        fields = [
            'id', 'profissional', 'dia_semana', 'dia_semana_display',
            'hora_entrada', 'hora_saida', 'intervalo_inicio', 'intervalo_fim', 'ativo',
        ]
        read_only_fields = ['profissional']


class ProfissionalSerializer(TextNormalizationMixin, BaseLojaSerializer):
    """Serializer de Profissional."""
    total_agendamentos = serializers.SerializerMethodField()
    horarios_trabalho = HorarioTrabalhoProfissionalSerializer(many=True, read_only=True, required=False)
    uppercase_fields = ['nome', 'especialidade']
    phone_fields = ['telefone']

    class Meta:
        model = Profissional
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']

    def get_total_agendamentos(self, obj):
        return obj.agendamentos.count()


class ProcedimentoSerializer(BaseLojaSerializer):
    """Serializer de Procedimento.
    Aceita 'duracao' como alias de 'duracao_minutos' para compatibilidade com o frontend.
    """

    total_protocolos = serializers.SerializerMethodField()

    class Meta:
        model = Procedimento
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']

    def get_total_protocolos(self, obj):
        return obj.protocolos.filter(is_active=True).count()

    def to_internal_value(self, data):
        """Aceita duracao como alias de duracao_minutos (frontend envia duracao)."""
        data = dict(data) if data else {}
        if 'duracao' in data and 'duracao_minutos' not in data:
            val = data.pop('duracao')
            if val is not None and val != '':
                try:
                    data['duracao_minutos'] = int(val) if isinstance(val, (int, float)) else int(str(val).strip())
                except (ValueError, TypeError):
                    pass  # Deixa a validação do campo tratar
        return super().to_internal_value(data)


class ProtocoloProcedimentoSerializer(BaseLojaSerializer):
    procedimento_nome = serializers.CharField(source='procedimento.nome', read_only=True)

    class Meta:
        model = ProtocoloProcedimento
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']


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


class FuncionarioSerializer(BaseLojaSerializer):
    class Meta:
        model = Funcionario
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']


class HistoricoLoginSerializer(BaseLojaSerializer):
    """
    Serializer para Histórico de Login
    Registra ações dos usuários com IP e detalhes
    """
    
    class Meta:
        model = HistoricoLogin
        fields = [
            'id', 'usuario', 'usuario_nome', 'acao', 'detalhes',
            'ip_address', 'user_agent', 'created_at', 'loja_id'
        ]
        read_only_fields = ['id', 'created_at', 'loja_id']
    
    def create(self, validated_data):
        """
        Adiciona loja_id automaticamente ao criar
        """
        return super().create(validated_data)
