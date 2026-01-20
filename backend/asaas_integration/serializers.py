"""
Serializers para integração com Asaas
"""
from rest_framework import serializers
from .models import AsaasCustomer, AsaasPayment, LojaAssinatura

class AsaasCustomerSerializer(serializers.ModelSerializer):
    """Serializer para clientes Asaas"""
    
    class Meta:
        model = AsaasCustomer
        fields = [
            'id', 'asaas_id', 'name', 'email', 'cpf_cnpj', 'phone',
            'address', 'address_number', 'complement', 'province',
            'city', 'state', 'postal_code', 'external_reference',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class AsaasPaymentSerializer(serializers.ModelSerializer):
    """Serializer para cobranças Asaas"""
    
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    billing_type_display = serializers.CharField(source='get_billing_type_display', read_only=True)
    is_paid = serializers.BooleanField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    is_pending = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = AsaasPayment
        fields = [
            'id', 'asaas_id', 'customer', 'customer_name', 'customer_email',
            'external_reference', 'billing_type', 'billing_type_display',
            'status', 'status_display', 'value', 'net_value',
            'due_date', 'payment_date', 'invoice_url', 'bank_slip_url',
            'pix_qr_code', 'pix_copy_paste', 'description',
            'is_paid', 'is_overdue', 'is_pending',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class LojaAssinaturaSerializer(serializers.ModelSerializer):
    """Serializer para assinaturas das lojas"""
    
    customer_data = AsaasCustomerSerializer(source='asaas_customer', read_only=True)
    current_payment_data = AsaasPaymentSerializer(source='current_payment', read_only=True)
    total_payments = serializers.SerializerMethodField()
    
    class Meta:
        model = LojaAssinatura
        fields = [
            'id', 'loja_slug', 'loja_nome', 'asaas_customer', 'customer_data',
            'current_payment', 'current_payment_data', 'plano_nome', 'plano_valor',
            'ativa', 'data_ativacao', 'data_vencimento', 'total_payments',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_payments(self, obj):
        """Retorna total de pagamentos desta assinatura"""
        return obj.get_all_payments().count()

class CreateLojaAssinaturaSerializer(serializers.Serializer):
    """Serializer para criar assinatura de loja"""
    
    loja = serializers.DictField(child=serializers.CharField())
    plano = serializers.DictField(child=serializers.CharField())
    
    def validate_loja(self, value):
        """Valida dados da loja"""
        required_fields = ['nome', 'slug', 'email', 'cpf_cnpj']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Campo '{field}' é obrigatório")
        return value
    
    def validate_plano(self, value):
        """Valida dados do plano"""
        required_fields = ['nome', 'preco']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Campo '{field}' é obrigatório")
        
        try:
            float(value['preco'])
        except (ValueError, TypeError):
            raise serializers.ValidationError("Preço deve ser um número válido")
        
        return value