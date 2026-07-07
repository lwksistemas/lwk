"""Serializers financeiros: CategoriaFinanceira, Transacao, TransacaoResumo."""
from rest_framework import serializers

from core.serializers import BaseLojaSerializer
from ..models import CategoriaFinanceira, Transacao


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
