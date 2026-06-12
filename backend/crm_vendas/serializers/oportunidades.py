"""Serializers de oportunidades CRM."""
from rest_framework import serializers

from core.serializer_mixins import (
    CpfCnpjNormalizationMixin,
    TextNormalizationMixin,
    UniqueDocumentoPerLojaMixin,
)

from ..models import Oportunidade

class OportunidadeSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    lead_nome = serializers.SerializerMethodField()
    vendedor_nome = serializers.CharField(source='vendedor.nome', read_only=True)
    conta_nome = serializers.SerializerMethodField()
    empresa_prestadora_nome = serializers.SerializerMethodField()

    uppercase_fields = ['titulo']

    class Meta:
        model = Oportunidade
        fields = [
            'id', 'titulo', 'lead', 'lead_nome', 'conta_nome',
            'empresa_prestadora', 'empresa_prestadora_nome',
            'valor', 'etapa', 'vendedor', 'vendedor_nome',
            'probabilidade', 'data_fechamento_prevista', 'data_fechamento',
            'data_fechamento_ganho', 'data_fechamento_perdido', 'valor_comissao',
            'observacoes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_lead_nome(self, obj):
        """Nome da pessoa (lead), não da empresa vinculada."""
        if obj.lead:
            return obj.lead.nome or ''
        return ''

    def get_conta_nome(self, obj):
        """Empresa do lead: PESSOA FISICA (CPF), campo empresa ou conta vinculada."""
        if not obj.lead:
            return None
        from core.cpf_utils import label_empresa_lead

        conta_nome = None
        if obj.lead.conta_id:
            try:
                conta_nome = obj.lead.conta.nome
            except Exception:
                pass
        return label_empresa_lead(
            obj.lead.cpf_cnpj,
            empresa=obj.lead.empresa,
            conta_nome=conta_nome,
        )

    def get_empresa_prestadora_nome(self, obj):
        """Retorna nome da empresa prestadora de serviço vinculada à oportunidade."""
        if obj.empresa_prestadora_id:
            try:
                return obj.empresa_prestadora.nome
            except Exception:
                pass
        return None

    def validate(self, attrs):
        """Empresa prestadora é obrigatória ao criar uma oportunidade."""
        # Só valida na criação (POST), não em updates parciais (PATCH)
        request = self.context.get('request')
        is_create = request and request.method == 'POST'
        if is_create and not attrs.get('empresa_prestadora'):
            raise serializers.ValidationError({
                'empresa_prestadora': 'Empresa prestadora é obrigatória. Selecione a empresa que irá prestar o serviço.'
            })
        return attrs

