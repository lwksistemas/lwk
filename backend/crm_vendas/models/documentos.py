from decimal import Decimal

from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin

from .oportunidades import Oportunidade


class Proposta(LojaIsolationMixin, models.Model):
    """Proposta comercial vinculada a uma oportunidade."""
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('enviada', 'Enviada'),
        ('aceita', 'Aceita'),
        ('pedido', 'Pedido'),
        ('rejeitada', 'Rejeitada'),
        ('cancelada', 'Cancelada'),
    ]
    
    STATUS_ASSINATURA_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('aguardando_cliente', 'Aguardando Cliente'),
        ('aguardando_vendedor', 'Aguardando Vendedor'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]

    DESCONTO_TIPO_CHOICES = [
        ('percentual', 'Percentual'),
        ('valor', 'Valor fixo'),
    ]

    oportunidade = models.ForeignKey(
        Oportunidade,
        on_delete=models.CASCADE,
        related_name='propostas',
    )
    numero = models.CharField(max_length=50, blank=True, help_text='Número sequencial da proposta (ex: 001, 002, 003)')
    titulo = models.CharField(max_length=255)
    conteudo = models.TextField(blank=True, help_text='Conteúdo da proposta em texto ou HTML')
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    desconto_tipo = models.CharField(
        max_length=15,
        choices=DESCONTO_TIPO_CHOICES,
        default='percentual',
        help_text='Tipo de desconto: percentual (%) ou valor fixo (R$)',
    )
    desconto_valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text='Valor do desconto (percentual ou fixo, conforme desconto_tipo)',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rascunho')
    motivo_cancelamento = models.TextField(blank=True, default='', help_text='Motivo do cancelamento da proposta')
    data_envio = models.DateTimeField(null=True, blank=True)
    data_resposta = models.DateTimeField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    nome_vendedor_assinatura = models.CharField(max_length=255, blank=True, help_text='Nome do vendedor para assinatura no PDF')
    nome_cliente_assinatura = models.CharField(max_length=255, blank=True, help_text='Nome do cliente para assinatura no PDF')
    emitente_nome = models.CharField(max_length=255, blank=True, default='', help_text='Snapshot: nome do emitente (vazio = dados da loja)')
    emitente_endereco = models.CharField(max_length=500, blank=True, default='')
    emitente_cpf_cnpj = models.CharField(max_length=18, blank=True, default='')
    emitente_responsavel = models.CharField(max_length=255, blank=True, default='')
    emitente_email = models.EmailField(blank=True, default='')
    status_assinatura = models.CharField(
        max_length=20,
        choices=STATUS_ASSINATURA_CHOICES,
        default='rascunho',
        help_text='Status do processo de assinatura digital'
    )
    canal_assinatura_vendedor = models.CharField(
        max_length=20,
        choices=[('email', 'E-mail'), ('whatsapp', 'WhatsApp')],
        default='email',
        help_text='Canal para enviar link de assinatura ao vendedor após o cliente assinar',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_vendas_proposta'
        ordering = ['-created_at']
        verbose_name = 'Proposta'
        verbose_name_plural = 'Propostas'
        indexes = [
            models.Index(fields=['loja_id', 'oportunidade'], name='crm_prop_loja_opor_idx'),
            models.Index(fields=['loja_id', 'status'], name='crm_prop_loja_status_idx'),
        ]

    def __str__(self):
        return f"{self.numero or self.titulo} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        """Gera número sequencial automaticamente se não fornecido."""
        # Garantir que loja_id está definido (chamando save do mixin primeiro se necessário)
        if not self.loja_id:
            from tenants.middleware import get_current_loja_id
            current_loja_id = get_current_loja_id()
            if current_loja_id:
                self.loja_id = current_loja_id
        
        # Gerar número se não fornecido e loja_id está disponível
        if not self.numero and self.loja_id:
            # Buscar o último número da loja
            ultima_proposta = Proposta.objects.filter(
                loja_id=self.loja_id
            ).exclude(numero='').order_by('-id').first()
            
            if ultima_proposta and ultima_proposta.numero:
                try:
                    ultimo_num = int(ultima_proposta.numero)
                    proximo_num = ultimo_num + 1
                except (ValueError, TypeError):
                    proximo_num = 1
            else:
                proximo_num = 1
            
            self.numero = str(proximo_num).zfill(3)  # 001, 002, 003, etc.
        
        super().save(*args, **kwargs)

    @property
    def valor_com_desconto(self):
        """Calcula o valor final após aplicar o desconto."""
        base = self.valor_total or Decimal('0')
        desconto = self.desconto_valor or Decimal('0')
        if desconto <= 0 or base <= 0:
            return base
        if self.desconto_tipo == 'percentual':
            return max(base - (base * desconto / Decimal('100')), Decimal('0'))
        return max(base - desconto, Decimal('0'))


class Contrato(LojaIsolationMixin, models.Model):
    """Contrato gerado a partir de oportunidade fechada como ganha."""
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('enviado', 'Enviado'),
        ('assinado', 'Assinado'),
        ('cancelado', 'Cancelado'),
    ]
    
    STATUS_ASSINATURA_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('aguardando_cliente', 'Aguardando Cliente'),
        ('aguardando_vendedor', 'Aguardando Vendedor'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]

    DESCONTO_TIPO_CHOICES = [
        ('percentual', 'Percentual'),
        ('valor', 'Valor fixo'),
    ]

    oportunidade = models.OneToOneField(
        Oportunidade,
        on_delete=models.CASCADE,
        related_name='contrato',
    )
    numero = models.CharField(max_length=50, blank=True)
    titulo = models.CharField(max_length=255)
    conteudo = models.TextField(blank=True, help_text='Conteúdo do contrato')
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    desconto_tipo = models.CharField(
        max_length=15,
        choices=DESCONTO_TIPO_CHOICES,
        default='percentual',
        help_text='Tipo de desconto: percentual (%) ou valor fixo (R$)',
    )
    desconto_valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text='Valor do desconto (percentual ou fixo, conforme desconto_tipo)',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rascunho')
    motivo_cancelamento = models.TextField(blank=True, default='', help_text='Motivo do cancelamento do contrato')
    data_envio = models.DateTimeField(null=True, blank=True)
    data_assinatura = models.DateTimeField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    nome_vendedor_assinatura = models.CharField(max_length=255, blank=True, help_text='Nome do vendedor para assinatura no PDF')
    nome_cliente_assinatura = models.CharField(max_length=255, blank=True, help_text='Nome do cliente para assinatura no PDF')
    emitente_nome = models.CharField(max_length=255, blank=True, default='', help_text='Snapshot: nome do emitente (vazio = dados da loja)')
    emitente_endereco = models.CharField(max_length=500, blank=True, default='')
    emitente_cpf_cnpj = models.CharField(max_length=18, blank=True, default='')
    emitente_responsavel = models.CharField(max_length=255, blank=True, default='')
    emitente_email = models.EmailField(blank=True, default='')
    status_assinatura = models.CharField(
        max_length=20,
        choices=STATUS_ASSINATURA_CHOICES,
        default='rascunho',
        help_text='Status do processo de assinatura digital'
    )
    canal_assinatura_vendedor = models.CharField(
        max_length=20,
        choices=[('email', 'E-mail'), ('whatsapp', 'WhatsApp')],
        default='email',
        help_text='Canal para enviar link de assinatura ao vendedor após o cliente assinar',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_vendas_contrato'
        ordering = ['-created_at']
        verbose_name = 'Contrato'
        verbose_name_plural = 'Contratos'
        indexes = [
            models.Index(fields=['loja_id', 'oportunidade'], name='crm_cont_loja_opor_idx'),
            models.Index(fields=['loja_id', 'status'], name='crm_cont_loja_status_idx'),
        ]

    def __str__(self):
        return f"{self.numero or self.titulo or 'Contrato'} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        """Gera número sequencial automaticamente se não fornecido."""
        # Garantir que loja_id está definido (chamando save do mixin primeiro se necessário)
        if not self.loja_id:
            from tenants.middleware import get_current_loja_id
            current_loja_id = get_current_loja_id()
            if current_loja_id:
                self.loja_id = current_loja_id
        
        # Gerar número se não fornecido e loja_id está disponível
        if not self.numero and self.loja_id:
            # Buscar o último número da loja
            ultimo_contrato = Contrato.objects.filter(
                loja_id=self.loja_id
            ).exclude(numero='').order_by('-id').first()
            
            if ultimo_contrato and ultimo_contrato.numero:
                try:
                    ultimo_num = int(ultimo_contrato.numero)
                    proximo_num = ultimo_num + 1
                except (ValueError, TypeError):
                    proximo_num = 1
            else:
                proximo_num = 1
            
            self.numero = str(proximo_num).zfill(3)  # 001, 002, 003, etc.
        
        super().save(*args, **kwargs)

    @property
    def valor_com_desconto(self):
        """Calcula o valor final após aplicar o desconto."""
        base = self.valor_total or Decimal('0')
        desconto = self.desconto_valor or Decimal('0')
        if desconto <= 0 or base <= 0:
            return base
        if self.desconto_tipo == 'percentual':
            return max(base - (base * desconto / Decimal('100')), Decimal('0'))
        return max(base - desconto, Decimal('0'))

