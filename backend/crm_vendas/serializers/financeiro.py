"""Serializers financeiro CRM."""
from rest_framework import serializers

from ..models.financeiro import GrupoFinanceiroCRM, LancamentoFinanceiroCRM


class GrupoFinanceiroCRMSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrupoFinanceiroCRM
        fields = ['id', 'nome', 'tipo', 'is_active', 'ordem', 'created_at']
        read_only_fields = ['id', 'created_at']


class LancamentoFinanceiroCRMSerializer(serializers.ModelSerializer):
    vendedor_nome = serializers.CharField(source='vendedor.nome', read_only=True)
    grupo_nome = serializers.CharField(source='grupo.nome', read_only=True, default='')
    origem_display = serializers.CharField(source='get_origem_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    oportunidade_titulo = serializers.CharField(
        source='oportunidade.titulo',
        read_only=True,
        default='',
    )
    editavel = serializers.SerializerMethodField()
    recorrente = serializers.BooleanField(write_only=True, required=False, default=False)
    frequencia = serializers.ChoiceField(
        write_only=True,
        required=False,
        default='mensal',
        choices=[('mensal', 'Mensal'), ('trimestral', 'Trimestral'), ('anual', 'Anual')],
    )
    data_fim_recorrencia = serializers.DateField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = LancamentoFinanceiroCRM
        fields = [
            'id',
            'vendedor',
            'vendedor_nome',
            'grupo',
            'grupo_nome',
            'tipo',
            'tipo_display',
            'origem',
            'origem_display',
            'descricao',
            'valor',
            'status',
            'status_display',
            'data_vencimento',
            'data_pagamento',
            'oportunidade',
            'oportunidade_titulo',
            'observacoes',
            'editavel',
            'recorrente',
            'frequencia',
            'data_fim_recorrencia',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'origem',
            'oportunidade',
            'created_at',
            'updated_at',
        ]

    def get_editavel(self, obj) -> bool:
        return obj.origem == LancamentoFinanceiroCRM.ORIGEM_MANUAL

    def validate(self, attrs):
        grupo = attrs.get('grupo') or getattr(self.instance, 'grupo', None)
        tipo = attrs.get('tipo') or getattr(self.instance, 'tipo', None)
        if grupo and tipo and grupo.tipo != tipo:
            raise serializers.ValidationError(
                {'grupo': 'O grupo selecionado não corresponde ao tipo do lançamento.'}
            )
        status = attrs.get('status')
        if status == LancamentoFinanceiroCRM.STATUS_PAGO and not attrs.get('data_pagamento'):
            if not (self.instance and self.instance.data_pagamento):
                from django.utils import timezone
                attrs['data_pagamento'] = timezone.now().date()
        return attrs
