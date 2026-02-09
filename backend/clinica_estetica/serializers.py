from rest_framework import serializers
from core.serializers import BaseLojaSerializer
from .models import (
    Cliente, Profissional, Procedimento, Agendamento, Funcionario,
    ProtocoloProcedimento, EvolucaoPaciente, AnamnesesTemplate, Anamnese,
    HorarioFuncionamento, BloqueioAgenda, Consulta, HistoricoLogin,
    CategoriaFinanceira, Transacao
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
    profissional_nome = serializers.CharField(source='profissional.nome', read_only=True, allow_null=True)
    
    # ✅ CORREÇÃO: Aceitar apenas ID como inteiro para evitar problema de schema
    # O DRF carrega objetos do schema errado quando usa ForeignKey diretamente
    profissional = serializers.IntegerField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = BloqueioAgenda
        fields = '__all__'
        read_only_fields = ['created_at', 'loja_id']  # loja_id é read-only (preenchido automaticamente)
    
    def validate_profissional(self, value):
        """
        Valida se o profissional existe na loja atual
        
        IMPORTANTE: Usa SQL direto com search_path explícito para garantir
        que estamos consultando o schema correto da loja.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if value is not None:
            from tenants.middleware import get_current_loja_id
            from django.db import connection
            from superadmin.models import Loja
            
            loja_id = get_current_loja_id()
            
            if not loja_id:
                raise serializers.ValidationError(
                    "Contexto de loja não encontrado"
                )
            
            logger.info(f"[BloqueioAgenda] Validando profissional_id={value} na loja_id={loja_id}")
            
            # Buscar schema da loja
            try:
                loja = Loja.objects.get(id=loja_id)
                schema_name = loja.database_name.replace('-', '_')
                logger.info(f"[BloqueioAgenda] Schema da loja: {schema_name}")
            except Loja.DoesNotExist:
                raise serializers.ValidationError(
                    f"Loja {loja_id} não encontrada"
                )
            
            # Consultar diretamente no schema correto usando SQL
            with connection.cursor() as cursor:
                cursor.execute(f"SET search_path TO {schema_name}, public")
                cursor.execute(
                    "SELECT EXISTS(SELECT 1 FROM clinica_profissionais WHERE id = %s AND is_active = true)",
                    [value]
                )
                existe = cursor.fetchone()[0]
            
            logger.info(f"[BloqueioAgenda] Profissional {value} existe no schema {schema_name}? {existe}")
            
            if not existe:
                logger.error(f"[BloqueioAgenda] ERRO: Profissional {value} não existe no schema {schema_name}")
                raise serializers.ValidationError(
                    f"Profissional ID {value} não existe nesta loja. "
                    f"Por favor, recarregue a página (Ctrl+Shift+R) e tente novamente."
                )
        
        return value
    
    def create(self, validated_data):
        """
        Cria bloqueio convertendo profissional_id para ForeignKey
        """
        import logging
        logger = logging.getLogger(__name__)
        
        profissional_id = validated_data.pop('profissional', None)
        
        # Criar bloqueio
        bloqueio = BloqueioAgenda(**validated_data)
        
        # Atribuir profissional_id diretamente (evita carregar objeto do schema errado)
        if profissional_id:
            bloqueio.profissional_id = profissional_id
            logger.info(f"[BloqueioAgenda] Criando bloqueio com profissional_id={profissional_id}")
        
        bloqueio.save()
        return bloqueio
    
    def update(self, instance, validated_data):
        """
        Atualiza bloqueio convertendo profissional_id para ForeignKey
        """
        profissional_id = validated_data.pop('profissional', None)
        
        # Atualizar campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Atualizar profissional_id
        if profissional_id is not None:
            instance.profissional_id = profissional_id
        
        instance.save()
        return instance


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



class CategoriaFinanceiraSerializer(BaseLojaSerializer):
    """
    Serializer para Categorias Financeiras
    Simples e direto (KISS - Keep It Simple)
    """
    
    class Meta:
        model = CategoriaFinanceira
        fields = ['id', 'nome', 'tipo', 'descricao', 'cor', 'is_active', 'created_at', 'loja_id']
        read_only_fields = ['id', 'created_at', 'loja_id']


class TransacaoSerializer(BaseLojaSerializer):
    """
    Serializer para Transações Financeiras
    Com campos calculados e relacionamentos
    """
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    categoria_cor = serializers.CharField(source='categoria.cor', read_only=True)
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    valor_pendente = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    esta_atrasado = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Transacao
        fields = [
            'id', 'tipo', 'descricao', 'categoria', 'categoria_nome', 'categoria_cor',
            'valor', 'valor_pago', 'valor_pendente', 'data_vencimento', 'data_pagamento',
            'status', 'forma_pagamento', 'cliente', 'cliente_nome', 'agendamento',
            'observacoes', 'anexo', 'is_recorrente', 'recorrencia_tipo',
            'esta_atrasado', 'created_at', 'updated_at', 'created_by', 'loja_id'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'loja_id', 'valor_pendente', 'esta_atrasado']
    
    def validate(self, data):
        """
        Validações customizadas (Clean Code)
        """
        # Validar que valor_pago não seja maior que valor
        valor = data.get('valor', 0)
        valor_pago = data.get('valor_pago', 0)
        
        if valor_pago > valor:
            raise serializers.ValidationError({
                'valor_pago': 'Valor pago não pode ser maior que o valor total'
            })
        
        # Se status é pago, exigir forma de pagamento
        if data.get('status') == 'pago' and not data.get('forma_pagamento'):
            raise serializers.ValidationError({
                'forma_pagamento': 'Forma de pagamento é obrigatória para transações pagas'
            })
        
        return data


class TransacaoResumoSerializer(serializers.Serializer):
    """
    Serializer para resumo financeiro (Dashboard)
    Apenas leitura, sem modelo (DTO Pattern)
    """
    total_receitas = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_despesas = serializers.DecimalField(max_digits=10, decimal_places=2)
    saldo = serializers.DecimalField(max_digits=10, decimal_places=2)
    receitas_pendentes = serializers.DecimalField(max_digits=10, decimal_places=2)
    despesas_pendentes = serializers.DecimalField(max_digits=10, decimal_places=2)
    receitas_pagas = serializers.DecimalField(max_digits=10, decimal_places=2)
    despesas_pagas = serializers.DecimalField(max_digits=10, decimal_places=2)
    transacoes_atrasadas = serializers.IntegerField()
    valor_atrasado = serializers.DecimalField(max_digits=10, decimal_places=2)
