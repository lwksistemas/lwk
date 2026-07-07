"""Serializers de agenda: Agendamento, BloqueioAgenda, Consulta."""
import re

from rest_framework import serializers

from core.serializers import BaseLojaSerializer
from ..models import Agendamento, BloqueioAgenda, Consulta


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
        agendamento = super().create(validated_data)
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


class BloqueioAgendaSerializer(serializers.ModelSerializer):
    tipo_nome = serializers.CharField(source='get_tipo_display', read_only=True)
    profissional_nome = serializers.CharField(source='profissional.nome', read_only=True, allow_null=True)
    
    # Campo profissional_id para leitura (retorna o ID do profissional)
    profissional_id = serializers.IntegerField(source='profissional.id', read_only=True, allow_null=True)
    
    # Campo profissional para escrita (aceita ID ao criar/atualizar)
    profissional = serializers.IntegerField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = BloqueioAgenda
        fields = '__all__'
        read_only_fields = ['created_at', 'loja_id']  # loja_id é read-only (preenchido automaticamente)
    
    def validate_profissional(self, value):
        """
        Valida se o profissional existe na loja atual.
        Usa SQL parametrizado com identifier quoting para prevenir SQL injection.
        """
        if value is not None:
            from tenants.middleware import get_current_loja_id
            from django.db import connection
            from django.utils.encoding import force_str
            from superadmin.models import Loja

            loja_id = get_current_loja_id()

            if not loja_id:
                raise serializers.ValidationError(
                    "Contexto de loja não encontrado"
                )

            try:
                loja = Loja.objects.get(id=loja_id)
                schema_name = loja.database_name.replace('-', '_')
            except Loja.DoesNotExist:
                raise serializers.ValidationError(
                    f"Loja {loja_id} não encontrada"
                )

            # Sanitizar schema_name: apenas alfanuméricos e underscore
            if not re.match(r'^[a-zA-Z0-9_]+$', schema_name):
                raise serializers.ValidationError("Nome de schema inválido")

            with connection.cursor() as cursor:
                cursor.execute(
                    "SET search_path TO %s, public" % connection.ops.quote_name(schema_name)
                )
                cursor.execute(
                    "SELECT EXISTS(SELECT 1 FROM clinica_profissionais WHERE id = %s AND is_active = true)",
                    [value]
                )
                existe = cursor.fetchone()[0]

            if not existe:
                raise serializers.ValidationError(
                    f"Profissional ID {value} não existe nesta loja. "
                    f"Por favor, recarregue a página (Ctrl+Shift+R) e tente novamente."
                )

        return value
    
    def create(self, validated_data):
        """Cria bloqueio convertendo profissional_id para ForeignKey."""
        profissional_id = validated_data.pop('profissional', None)
        bloqueio = BloqueioAgenda(**validated_data)
        if profissional_id:
            bloqueio.profissional_id = profissional_id
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


class ConsultaSerializer(serializers.ModelSerializer):
    """Serializer para consultas"""
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    profissional_nome = serializers.CharField(source='profissional.nome', read_only=True)
    procedimento_nome = serializers.CharField(source='procedimento.nome', read_only=True)
    agendamento_data = serializers.DateField(source='agendamento.data', read_only=True)
    agendamento_horario = serializers.TimeField(source='agendamento.horario', read_only=True)
    agendamento_status = serializers.CharField(source='agendamento.status', read_only=True)
    duracao_minutos = serializers.ReadOnlyField()
    total_evolucoes = serializers.SerializerMethodField()

    class Meta:
        model = Consulta
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_total_evolucoes(self, obj):
        return obj.evolucoes.count()
