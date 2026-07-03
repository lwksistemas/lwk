from django.db import models

from core.mixins import LojaIsolationMixin, LojaIsolationManager

from .contas import Conta

class Lead(LojaIsolationMixin, models.Model):
    """Lead (potencial cliente)."""
    # Choices mantidas para referência, mas não mais usadas no campo
    # As origens são configuráveis via CRMConfig.origens_leads
    ORIGEM_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('site', 'Site'),
        ('indicacao', 'Indicação'),
        ('outro', 'Outro'),
    ]
    STATUS_CHOICES = [
        ('novo', 'Novo'),
        ('contato', 'Contato feito'),
        ('qualificado', 'Qualificado'),
        ('perdido', 'Perdido'),
    ]

    nome = models.CharField(max_length=200)
    empresa = models.CharField(max_length=200, blank=True)
    cpf_cnpj = models.CharField(max_length=18, blank=True, help_text='CPF ou CNPJ do lead')
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True)
    origem = models.CharField(
        max_length=50,
        default='site',
        help_text='Origem do lead (valores configuráveis via CRMConfig)'
    )
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='novo')
    valor_estimado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    conta = models.ForeignKey(
        Conta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads',
    )
    contato = models.ForeignKey(
        'Contato',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads',
        help_text='Contato específico vinculado ao lead',
    )
    vendedor = models.ForeignKey(
        'Vendedor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads',
        help_text='Vendedor responsável pelo lead (quando criado por vendedor)',
    )
    observacoes = models.TextField(blank=True)
    # Endereço
    cep = models.CharField(max_length=10, blank=True)
    logradouro = models.CharField(max_length=200, blank=True)
    numero = models.CharField(max_length=20, blank=True)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    uf = models.CharField(max_length=2, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_vendas_lead'
        ordering = ['nome']
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        indexes = [
            models.Index(fields=['loja_id', 'status'], name='crm_lead_loja_status_idx'),
            models.Index(fields=['loja_id', 'origem'], name='crm_lead_loja_origem_idx'),
            models.Index(fields=['loja_id', 'vendedor'], name='crm_lead_loja_vend_idx'),
            models.Index(fields=['loja_id', 'created_at'], name='crm_lead_loja_created_idx'),
            models.Index(fields=['loja_id', 'conta'], name='crm_lead_loja_conta_idx'),
            models.Index(fields=['loja_id', 'contato'], name='crm_lead_loja_contato_idx'),
            models.Index(fields=['loja_id', 'cpf_cnpj'], name='crm_lead_loja_cpfcnpj_idx'),
        ]

    def __str__(self):
        return f"{self.nome} ({self.empresa or '-'})"

