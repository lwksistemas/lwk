"""Modelos Super Admin."""

from django.db import models

from .loja import Loja


class FinanceiroLoja(models.Model):
    """Controle financeiro de cada loja"""
    loja = models.OneToOneField(Loja, on_delete=models.CASCADE, related_name='financeiro')
    
    # Assinatura
    data_proxima_cobranca = models.DateField()
    valor_mensalidade = models.DecimalField(max_digits=10, decimal_places=2)
    dia_vencimento = models.IntegerField(default=10)  # Dia do mês
    
    # Status de pagamento
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('pendente', 'Pagamento Pendente'),
        ('atrasado', 'Atrasado'),
        ('suspenso', 'Suspenso'),
        ('cancelado', 'Cancelado'),
    ]
    status_pagamento = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')
    
    # Provedor de boleto: asaas ou mercadopago
    PROVEDOR_BOLETO_CHOICES = [
        ('asaas', 'Asaas'),
        ('mercadopago', 'Mercado Pago'),
    ]
    provedor_boleto = models.CharField(
        max_length=20, choices=PROVEDOR_BOLETO_CHOICES, default='asaas',
        help_text='Provedor usado para gerar boleto desta cobrança'
    )
    mercadopago_payment_id = models.CharField(max_length=100, blank=True, help_text='ID do pagamento boleto no Mercado Pago')
    mercadopago_pix_payment_id = models.CharField(max_length=100, blank=True, help_text='ID do pagamento PIX no Mercado Pago')
    
    # Integração Asaas
    asaas_customer_id = models.CharField(max_length=100, blank=True, help_text='ID do cliente no Asaas')
    asaas_payment_id = models.CharField(max_length=100, blank=True, help_text='ID do pagamento atual no Asaas')
    boleto_url = models.URLField(blank=True, help_text='URL do boleto (Asaas ou Mercado Pago)')
    boleto_pdf_url = models.URLField(blank=True, help_text='URL do PDF do boleto')
    pix_qr_code = models.TextField(blank=True, help_text='QR Code PIX')
    pix_copy_paste = models.TextField(blank=True, help_text='PIX Copia e Cola')
    
    # ✅ NOVO: Cartão de crédito (Asaas)
    asaas_creditcard_token = models.CharField(
        max_length=100, 
        blank=True, 
        help_text='Token do cartão tokenizado no Asaas para cobranças recorrentes'
    )
    cartao_ultimos_digitos = models.CharField(
        max_length=4, 
        blank=True, 
        help_text='Últimos 4 dígitos do cartão (para exibição)'
    )
    cartao_bandeira = models.CharField(
        max_length=20, 
        blank=True, 
        help_text='Bandeira do cartão (Visa, Mastercard, Elo, etc)'
    )
    link_pagamento_cartao = models.URLField(
        blank=True, 
        help_text='Link para página de cadastro do cartão (enviado após primeiro pagamento)'
    )
    cartao_cadastrado = models.BooleanField(
        default=False, 
        help_text='Indica se o cartão já foi cadastrado e tokenizado'
    )
    cartao_cadastrado_em = models.DateTimeField(
        null=True, 
        blank=True, 
        help_text='Data e hora em que o cartão foi cadastrado'
    )
    
    # Totalizadores
    total_pago = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_pendente = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Controle de sincronização
    last_sync_at = models.DateTimeField(null=True, blank=True, help_text='Última sincronização com Asaas')
    sync_error = models.TextField(blank=True, help_text='Último erro de sincronização')
    
    # Dados de pagamento
    forma_pagamento = models.CharField(max_length=50, blank=True)  # cartao, boleto, pix
    ultimo_pagamento = models.DateTimeField(null=True, blank=True)
    
    # Controle de envio de senha provisória
    senha_enviada = models.BooleanField(default=False, help_text='Indica se a senha provisória já foi enviada')
    data_envio_senha = models.DateTimeField(null=True, blank=True, help_text='Data e hora do envio da senha provisória')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Financeiro da Loja'
        verbose_name_plural = 'Financeiros das Lojas'
        # ✅ OTIMIZAÇÃO: Índices para queries comuns
        indexes = [
            models.Index(fields=['status_pagamento', 'data_proxima_cobranca'], name='fin_status_data_idx'),
            models.Index(fields=['loja', 'status_pagamento'], name='fin_loja_status_idx'),
            models.Index(fields=['asaas_customer_id'], name='fin_asaas_customer_idx'),
            models.Index(fields=['asaas_payment_id'], name='fin_asaas_payment_idx'),
            models.Index(fields=['mercadopago_payment_id'], name='fin_mp_payment_idx'),
        ]
    
    def __str__(self):
        return f"Financeiro - {self.loja.nome}"


class PagamentoLoja(models.Model):
    """Histórico de pagamentos de cada loja"""
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='pagamentos')
    financeiro = models.ForeignKey(FinanceiroLoja, on_delete=models.CASCADE, related_name='pagamentos')
    
    # Dados do pagamento
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    referencia_mes = models.DateField()  # Mês de referência
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('atrasado', 'Atrasado'),
        ('cancelado', 'Cancelado'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    
    # Provedor do boleto
    provedor_boleto = models.CharField(
        max_length=20,
        choices=FinanceiroLoja.PROVEDOR_BOLETO_CHOICES,
        default='asaas',
        help_text='Provedor do boleto (Asaas ou Mercado Pago)'
    )
    mercadopago_payment_id = models.CharField(max_length=100, blank=True, help_text='ID do pagamento boleto no Mercado Pago')
    mercadopago_pix_payment_id = models.CharField(max_length=100, blank=True, help_text='ID do pagamento PIX no Mercado Pago')
    
    # Integração Asaas
    asaas_payment_id = models.CharField(max_length=100, blank=True, help_text='ID do pagamento no Asaas')
    boleto_url = models.URLField(blank=True, help_text='URL do boleto')
    boleto_pdf_url = models.URLField(blank=True, help_text='URL do PDF do boleto')
    pix_qr_code = models.TextField(blank=True, help_text='QR Code PIX')
    pix_copy_paste = models.TextField(blank=True, help_text='PIX Copia e Cola')
    
    # Detalhes
    forma_pagamento = models.CharField(max_length=50)
    comprovante = models.URLField(blank=True)
    observacoes = models.TextField(blank=True)
    
    # Datas
    data_vencimento = models.DateField()
    data_pagamento = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
        ordering = ['-data_vencimento']
        # ✅ OTIMIZAÇÃO: Índices para queries comuns
        indexes = [
            models.Index(fields=['loja', 'status', '-data_vencimento'], name='pag_loja_status_idx'),
            models.Index(fields=['status', 'data_vencimento'], name='pag_status_venc_idx'),
            models.Index(fields=['financeiro', '-data_vencimento'], name='pag_fin_venc_idx'),
            models.Index(fields=['asaas_payment_id'], name='pag_asaas_payment_idx'),
            models.Index(fields=['mercadopago_payment_id'], name='pag_mp_payment_idx'),
        ]
    
    def __str__(self):
        return f"{self.loja.nome} - {self.referencia_mes.strftime('%m/%Y')} - R$ {self.valor}"


