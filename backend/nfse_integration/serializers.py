"""
Serializers para NFS-e
"""
from rest_framework import serializers
from .models import NFSe


class NFSeSerializer(serializers.ModelSerializer):
    """Serializer para NFS-e."""
    
    valor_liquido = serializers.SerializerMethodField()
    provedor_display = serializers.CharField(source='get_provedor_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = NFSe
        fields = [
            'id', 'numero_nf', 'numero_rps', 'codigo_verificacao',
            'data_emissao', 'data_cancelamento',
            'valor', 'valor_iss', 'aliquota_iss', 'valor_liquido',
            'tomador_cpf_cnpj', 'tomador_nome', 'tomador_email',
            'servico_codigo', 'servico_descricao',
            'provedor', 'provedor_display',
            'status', 'status_display',
            'pdf_url', 'xml_url',
            'observacoes', 'erro',
            'asaas_invoice_id', 'asaas_payment_id',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero_nf', 'numero_rps', 'codigo_verificacao',
            'data_emissao', 'data_cancelamento',
            'valor_iss', 'xml_rps', 'xml_nfse',
            'asaas_invoice_id', 'asaas_payment_id',
            'created_at', 'updated_at',
        ]
    
    def get_valor_liquido(self, obj):
        """Retorna valor líquido (valor - ISS)."""
        return float(obj.get_valor_liquido())


class EmitirNFSeSerializer(serializers.Serializer):
    """Serializer para emissão de NFS-e."""
    
    # Opção 1: Selecionar conta cadastrada
    conta_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text='ID da conta (empresa) cadastrada no CRM'
    )
    
    # Opção 2: Preencher manualmente
    tomador_cpf_cnpj = serializers.CharField(
        max_length=18,
        required=False,
        allow_blank=True,
        help_text='CPF ou CNPJ do tomador (obrigatório se não informar conta_id)'
    )
    tomador_nome = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        help_text='Nome ou razão social do tomador'
    )
    tomador_email = serializers.EmailField(
        required=False,
        allow_blank=True,
        help_text='Email do tomador'
    )
    
    # Endereço do tomador
    tomador_logradouro = serializers.CharField(max_length=255, required=False, allow_blank=True)
    tomador_numero = serializers.CharField(max_length=20, required=False, allow_blank=True)
    tomador_complemento = serializers.CharField(max_length=100, required=False, allow_blank=True)
    tomador_bairro = serializers.CharField(max_length=100, required=False, allow_blank=True)
    tomador_cidade = serializers.CharField(max_length=100, required=False, allow_blank=True)
    tomador_uf = serializers.CharField(max_length=2, required=False, allow_blank=True)
    tomador_cep = serializers.CharField(max_length=10, required=False, allow_blank=True)
    
    # Dados do serviço
    servico_descricao = serializers.CharField(
        required=True,
        help_text='Descrição do serviço prestado'
    )
    valor_servicos = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        help_text='Valor total dos serviços'
    )
    
    # Opções
    enviar_email = serializers.BooleanField(
        default=True,
        help_text='Se True, envia email para o tomador com a NF'
    )
    
    def validate(self, data):
        """Valida que ou conta_id ou dados manuais foram fornecidos."""
        conta_id = data.get('conta_id')
        tomador_cpf_cnpj = data.get('tomador_cpf_cnpj')
        
        if not conta_id and not tomador_cpf_cnpj:
            raise serializers.ValidationError({
                'conta_id': 'Informe uma conta cadastrada ou preencha os dados manualmente',
                'tomador_cpf_cnpj': 'Informe uma conta cadastrada ou preencha os dados manualmente'
            })
        
        # Se preencheu manualmente, validar campos obrigatórios
        if not conta_id:
            if not data.get('tomador_nome'):
                raise serializers.ValidationError({
                    'tomador_nome': 'Nome do tomador é obrigatório'
                })
            if not data.get('tomador_cidade'):
                raise serializers.ValidationError({
                    'tomador_cidade': 'Cidade do tomador é obrigatória'
                })
            if not data.get('tomador_uf'):
                raise serializers.ValidationError({
                    'tomador_uf': 'UF do tomador é obrigatório'
                })
        
        return data


class CancelarNFSeSerializer(serializers.Serializer):
    """Serializer para cancelamento de NFS-e."""
    
    motivo = serializers.CharField(
        required=True,
        max_length=255,
        help_text='Motivo do cancelamento'
    )
