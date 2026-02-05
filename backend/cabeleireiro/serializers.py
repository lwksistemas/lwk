from rest_framework import serializers
from core.serializers import BaseLojaSerializer
from .models import (
    Cliente, Profissional, Servico, Agendamento, Produto, Venda,
    Funcionario, HorarioFuncionamento, BloqueioAgenda
)


class ClienteSerializer(BaseLojaSerializer):
    """Serializer de Cliente - herda BaseLojaSerializer para adicionar loja_id automaticamente"""
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


class ClienteBuscaSerializer(serializers.ModelSerializer):
    """Serializer simplificado para busca de clientes"""
    class Meta:
        model = Cliente
        fields = ['id', 'nome', 'telefone', 'email']


class ProfissionalSerializer(BaseLojaSerializer):
    """Serializer de Profissional"""
    total_agendamentos = serializers.SerializerMethodField()
    total_atendimentos_mes = serializers.SerializerMethodField()

    class Meta:
        model = Profissional
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']

    def get_total_agendamentos(self, obj):
        return obj.agendamentos.count()

    def get_total_atendimentos_mes(self, obj):
        from datetime import date
        hoje = date.today()
        return obj.agendamentos.filter(
            data__year=hoje.year,
            data__month=hoje.month,
            status='concluido'
        ).count()


class ServicoSerializer(BaseLojaSerializer):
    """Serializer de Serviço"""
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    total_agendamentos = serializers.SerializerMethodField()

    class Meta:
        model = Servico
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']

    def get_total_agendamentos(self, obj):
        return obj.agendamentos.count()


class AgendamentoSerializer(BaseLojaSerializer):
    """Serializer de Agendamento"""
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    cliente_telefone = serializers.CharField(source='cliente.telefone', read_only=True)
    profissional_nome = serializers.CharField(source='profissional.nome', read_only=True)
    servico_nome = serializers.CharField(source='servico.nome', read_only=True)
    servico_duracao = serializers.IntegerField(source='servico.duracao_minutos', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Agendamento
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']


class ProdutoSerializer(BaseLojaSerializer):
    """Serializer de Produto"""
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    margem_lucro = serializers.SerializerMethodField()
    estoque_baixo = serializers.SerializerMethodField()

    class Meta:
        model = Produto
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']

    def get_margem_lucro(self, obj):
        if obj.preco_custo > 0:
            return ((obj.preco_venda - obj.preco_custo) / obj.preco_custo) * 100
        return 0

    def get_estoque_baixo(self, obj):
        return obj.estoque_atual <= obj.estoque_minimo


class VendaSerializer(BaseLojaSerializer):
    """Serializer de Venda"""
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True, allow_null=True)
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    forma_pagamento_display = serializers.CharField(source='get_forma_pagamento_display', read_only=True)

    class Meta:
        model = Venda
        fields = '__all__'
        read_only_fields = ['data_venda', 'valor_total', 'loja_id']


class FuncionarioSerializer(BaseLojaSerializer):
    """Serializer de Funcionário"""
    tempo_empresa = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    funcao_display = serializers.CharField(source='get_funcao_display', read_only=True)
    is_profissional = serializers.BooleanField(read_only=True)

    class Meta:
        model = Funcionario
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']

    def get_tempo_empresa(self, obj):
        from datetime import date
        hoje = date.today()
        delta = hoje - obj.data_admissao
        anos = delta.days // 365
        meses = (delta.days % 365) // 30
        return f"{anos} anos e {meses} meses"
    
    def get_is_admin(self, obj):
        """Verifica se o funcionário é o administrador da loja"""
        from superadmin.models import Loja
        try:
            loja = Loja.objects.get(id=obj.loja_id)
            return obj.email == loja.owner.email
        except:
            return False


class HorarioFuncionamentoSerializer(BaseLojaSerializer):
    """Serializer de Horário de Funcionamento"""
    dia_semana_display = serializers.CharField(source='get_dia_semana_display', read_only=True)

    class Meta:
        model = HorarioFuncionamento
        fields = '__all__'
        read_only_fields = ['loja_id']


class BloqueioAgendaSerializer(BaseLojaSerializer):
    """Serializer de Bloqueio de Agenda"""
    profissional_nome = serializers.CharField(source='profissional.nome', read_only=True)

    class Meta:
        model = BloqueioAgenda
        fields = '__all__'
        read_only_fields = ['loja_id']
