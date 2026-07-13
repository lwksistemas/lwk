"""Serializers de leads CRM."""
from rest_framework import serializers

from core.serializer_mixins import (
    CpfCnpjNormalizationMixin,
    TextNormalizationMixin,
    UniqueDocumentoPerLojaMixin,
)

from ..models import Lead


class LeadSerializer(
    UniqueDocumentoPerLojaMixin,
    CpfCnpjNormalizationMixin,
    TextNormalizationMixin,
    serializers.ModelSerializer,
):
    unique_documento_fields = ['cpf_cnpj']
    unique_documento_entidade = 'lead'
    conta_info = serializers.SerializerMethodField()
    contato_info = serializers.SerializerMethodField()
    phone_fields = ['telefone']
    uppercase_fields = ['nome', 'empresa', 'cidade', 'bairro', 'uf']
    
    class Meta:
        model = Lead
        fields = [
            'id', 'nome', 'empresa', 'cpf_cnpj', 'email', 'telefone', 'origem', 'status',
            'valor_estimado', 'conta', 'conta_info', 'contato', 'contato_info', 'observacoes',
            'cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'uf',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_conta_info(self, obj):
        """Retorna informações completas da conta vinculada."""
        if obj.conta:
            return {
                'id': obj.conta.id,
                'nome': obj.conta.nome,
                'razao_social': obj.conta.razao_social,
                'cnpj': obj.conta.cnpj,
                'inscricao_estadual': obj.conta.inscricao_estadual,
                'email': obj.conta.email,
                'telefone': obj.conta.telefone,
                'site': obj.conta.site,
                'cep': obj.conta.cep,
                'logradouro': obj.conta.logradouro,
                'numero': obj.conta.numero,
                'complemento': obj.conta.complemento,
                'bairro': obj.conta.bairro,
                'cidade': obj.conta.cidade,
                'uf': obj.conta.uf,
            }
        return None
    
    def get_contato_info(self, obj):
        """Retorna informações do contato vinculado."""
        if obj.contato:
            return {
                'id': obj.contato.id,
                'nome': obj.contato.nome,
                'email': obj.contato.email,
                'telefone': obj.contato.telefone,
                'cargo': obj.contato.cargo,
            }
        return None


class LeadListSerializer(CpfCnpjNormalizationMixin, TextNormalizationMixin, serializers.ModelSerializer):
    conta_nome = serializers.CharField(source='conta.nome', read_only=True)
    conta_cnpj = serializers.CharField(source='conta.cnpj', read_only=True)
    conta_razao_social = serializers.CharField(source='conta.razao_social', read_only=True)
    contato_nome = serializers.CharField(source='contato.nome', read_only=True)
    phone_fields = ['telefone']
    uppercase_fields = ['nome', 'empresa', 'cidade', 'bairro', 'uf']

    class Meta:
        model = Lead
        fields = [
            'id', 'nome', 'empresa', 'cpf_cnpj', 'email', 'telefone', 'origem', 'status', 'valor_estimado',
            'conta', 'conta_nome', 'conta_cnpj', 'conta_razao_social', 'contato', 'contato_nome',
            'cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'uf',
            'created_at',
        ]
