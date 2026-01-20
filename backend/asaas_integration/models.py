"""
Modelos para integração com Asaas
Armazena dados de cobranças e pagamentos
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import json

class AsaasConfig(models.Model):
    """Configuração da integração Asaas"""
    
    # Chave única para garantir apenas uma configuração
    singleton_key = models.CharField(max_length=10, default='config', unique=True)
    
    # Configurações da API
    api_key = models.TextField(verbose_name="Chave da API Asaas")
    sandbox = models.BooleanField(default=True, verbose_name="Ambiente Sandbox")
    enabled = models.BooleanField(default=False, verbose_name="Integração Habilitada")
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    last_sync = models.DateTimeField(null=True, blank=True, verbose_name="Última Sincronização")
    
    class Meta:
        verbose_name = "Configuração Asaas"
        verbose_name_plural = "Configurações Asaas"
        db_table = 'asaas_config'
    
    def save(self, *args, **kwargs):
        # Auto-detectar sandbox baseado na chave
        if self.api_key:
            self.sandbox = 'hmlg' in self.api_key
        
        # Validar formato da chave
        if self.api_key and not self.api_key.startswith('$aact_'):
            raise ValidationError('Chave API deve começar com $aact_')
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        env = "Sandbox" if self.sandbox else "Produção"
        status = "Habilitada" if self.enabled else "Desabilitada"
        return f"Configuração Asaas - {env} - {status}"
    
    @classmethod
    def get_config(cls):
        """Obter ou criar configuração única"""
        config, created = cls.objects.get_or_create(
            singleton_key='config',
            defaults={
                'api_key': '',
                'sandbox': True,
                'enabled': False
            }
        )
        return config
    
    @property
    def api_key_masked(self):
        """Retorna chave mascarada para exibição"""
        if not self.api_key:
            return ''
        if len(self.api_key) <= 14:
            return self.api_key
        return f"{self.api_key[:10]}...{self.api_key[-4:]}"
    
    @property
    def environment_name(self):
        """Nome do ambiente"""
        return "Sandbox" if self.sandbox else "Produção"

class AsaasCustomer(models.Model):
    """Cliente no Asaas"""
    
    asaas_id = models.CharField(max_length=100, unique=True, verbose_name="ID no Asaas")
    name = models.CharField(max_length=200, verbose_name="Nome")
    email = models.EmailField(verbose_name="Email")
    cpf_cnpj = models.CharField(max_length=20, verbose_name="CPF/CNPJ")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    
    # Endereço
    address = models.CharField(max_length=200, blank=True, verbose_name="Endereço")
    address_number = models.CharField(max_length=20, blank=True, verbose_name="Número")
    complement = models.CharField(max_length=100, blank=True, verbose_name="Complemento")
    province = models.CharField(max_length=100, blank=True, verbose_name="Bairro")
    city = models.CharField(max_length=100, blank=True, verbose_name="Cidade")
    state = models.CharField(max_length=2, blank=True, verbose_name="Estado")
    postal_code = models.CharField(max_length=10, blank=True, verbose_name="CEP")
    
    # Referência externa (slug da loja)
    external_reference = models.CharField(max_length=100, blank=True, verbose_name="Referência Externa")
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    raw_data = models.JSONField(default=dict, verbose_name="Dados Brutos do Asaas")
    
    class Meta:
        verbose_name = "Cliente Asaas"
        verbose_name_plural = "Clientes Asaas"
        db_table = 'asaas_customer'
    
    def __str__(self):
        return f"{self.name} ({self.asaas_id})"

class AsaasPayment(models.Model):
    """Cobrança no Asaas"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Aguardando pagamento'),
        ('RECEIVED', 'Recebida'),
        ('CONFIRMED', 'Pagamento confirmado'),
        ('OVERDUE', 'Vencida'),
        ('REFUNDED', 'Estornada'),
        ('RECEIVED_IN_CASH', 'Recebida à vista'),
        ('REFUND_REQUESTED', 'Estorno solicitado'),
        ('REFUND_IN_PROGRESS', 'Estorno em processamento'),
        ('CHARGEBACK_REQUESTED', 'Chargeback solicitado'),
        ('CHARGEBACK_DISPUTE', 'Em disputa de chargeback'),
        ('AWAITING_CHARGEBACK_REVERSAL', 'Aguardando reversão do chargeback'),
        ('DUNNING_REQUESTED', 'Cobrança solicitada'),
        ('DUNNING_RECEIVED', 'Cobrança recebida'),
        ('AWAITING_RISK_ANALYSIS', 'Aguardando análise'),
    ]
    
    BILLING_TYPE_CHOICES = [
        ('BOLETO', 'Boleto'),
        ('CREDIT_CARD', 'Cartão de Crédito'),
        ('PIX', 'PIX'),
        ('UNDEFINED', 'Não definido'),
    ]
    
    # Identificadores
    asaas_id = models.CharField(max_length=100, unique=True, verbose_name="ID no Asaas")
    customer = models.ForeignKey(AsaasCustomer, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Cliente")
    external_reference = models.CharField(max_length=100, blank=True, verbose_name="Referência Externa")
    
    # Dados da cobrança
    billing_type = models.CharField(max_length=20, choices=BILLING_TYPE_CHOICES, verbose_name="Tipo de Cobrança")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, verbose_name="Status")
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    net_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Valor Líquido")
    
    # Datas
    due_date = models.DateField(null=True, blank=True, verbose_name="Data de Vencimento")
    payment_date = models.DateTimeField(null=True, blank=True, verbose_name="Data do Pagamento")
    
    # URLs e dados de pagamento
    invoice_url = models.URLField(blank=True, verbose_name="URL da Fatura")
    bank_slip_url = models.URLField(blank=True, verbose_name="URL do Boleto")
    
    # PIX
    pix_qr_code = models.TextField(blank=True, verbose_name="QR Code PIX")
    pix_copy_paste = models.TextField(blank=True, verbose_name="PIX Copia e Cola")
    
    # Descrição
    description = models.TextField(blank=True, verbose_name="Descrição")
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    raw_data = models.JSONField(default=dict, verbose_name="Dados Brutos do Asaas")
    
    class Meta:
        verbose_name = "Cobrança Asaas"
        verbose_name_plural = "Cobranças Asaas"
        db_table = 'asaas_payment'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Cobrança {self.asaas_id} - R$ {self.value}"
    
    @property
    def is_paid(self):
        """Verifica se a cobrança foi paga"""
        return self.status in ['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH']
    
    @property
    def is_overdue(self):
        """Verifica se a cobrança está vencida"""
        return self.status == 'OVERDUE'
    
    @property
    def is_pending(self):
        """Verifica se a cobrança está pendente"""
        return self.status == 'PENDING'

class LojaAssinatura(models.Model):
    """Relaciona loja com assinatura no Asaas"""
    
    # Referência à loja (usando external_reference para evitar dependência circular)
    loja_slug = models.CharField(max_length=100, unique=True, verbose_name="Slug da Loja")
    loja_nome = models.CharField(max_length=200, verbose_name="Nome da Loja")
    
    # Cliente e pagamentos no Asaas
    asaas_customer = models.ForeignKey(AsaasCustomer, on_delete=models.CASCADE, verbose_name="Cliente Asaas")
    current_payment = models.ForeignKey(AsaasPayment, null=True, blank=True, on_delete=models.SET_NULL, 
                                       related_name='current_subscription', verbose_name="Pagamento Atual")
    
    # Dados do plano
    plano_nome = models.CharField(max_length=100, verbose_name="Nome do Plano")
    plano_valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor do Plano")
    
    # Status da assinatura
    ativa = models.BooleanField(default=True, verbose_name="Assinatura Ativa")
    data_ativacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Ativação")
    data_vencimento = models.DateField(null=True, blank=True, verbose_name="Data de Vencimento")
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        verbose_name = "Assinatura da Loja"
        verbose_name_plural = "Assinaturas das Lojas"
        db_table = 'loja_assinatura'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Assinatura {self.loja_nome} - {self.plano_nome}"
    
    def get_all_payments(self):
        """Retorna todos os pagamentos desta assinatura"""
        return AsaasPayment.objects.filter(
            external_reference__contains=f"loja_{self.loja_slug}"
        ).order_by('-created_at')