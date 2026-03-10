"""
Modelos do CRM Vendas - multi-tenant (LojaIsolationMixin).
Compatível com dashboard estilo Salesforce: Leads, Contas, Contatos,
Oportunidades, Pipeline, Atividades, Vendedores.
"""
from django.db import models
from django.conf import settings
from core.mixins import LojaIsolationMixin, LojaIsolationManager


class Vendedor(LojaIsolationMixin, models.Model):
    """Vendedor da loja (equipe de vendas)."""
    nome = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True)
    cargo = models.CharField(max_length=100, default='Vendedor')
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_vendas_vendedor'
        ordering = ['nome']
        verbose_name = 'Vendedor'
        verbose_name_plural = 'Vendedores'
        indexes = [
            models.Index(fields=['loja_id', 'is_active'], name='crm_vend_loja_active_idx'),
            models.Index(fields=['loja_id', 'email'], name='crm_vend_loja_email_idx'),
        ]

    def __str__(self):
        return self.nome


class Conta(LojaIsolationMixin, models.Model):
    """Conta (empresa)."""
    nome = models.CharField(max_length=255)
    vendedor = models.ForeignKey(
        'Vendedor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contas',
        help_text='Vendedor responsável pela conta (quando criado por vendedor)',
    )
    segmento = models.CharField(max_length=100, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True)
    endereco = models.CharField(max_length=255, blank=True)
    observacoes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_vendas_conta'
        ordering = ['nome']
        verbose_name = 'Conta'
        verbose_name_plural = 'Contas'
        indexes = [
            models.Index(fields=['loja_id', 'nome'], name='crm_conta_loja_nome_idx'),
            models.Index(fields=['loja_id', 'vendedor'], name='crm_conta_loja_vend_idx'),
            models.Index(fields=['loja_id', 'created_at'], name='crm_conta_loja_created_idx'),
        ]

    def __str__(self):
        return self.nome


class Lead(LojaIsolationMixin, models.Model):
    """Lead (potencial cliente)."""
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
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True)
    origem = models.CharField(max_length=50, choices=ORIGEM_CHOICES, default='site')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='novo')
    valor_estimado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    conta = models.ForeignKey(
        Conta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads',
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_vendas_lead'
        ordering = ['-created_at']
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        indexes = [
            models.Index(fields=['loja_id', 'status'], name='crm_lead_loja_status_idx'),
            models.Index(fields=['loja_id', 'origem'], name='crm_lead_loja_origem_idx'),
            models.Index(fields=['loja_id', 'vendedor'], name='crm_lead_loja_vend_idx'),
            models.Index(fields=['loja_id', 'created_at'], name='crm_lead_loja_created_idx'),
            models.Index(fields=['loja_id', 'conta'], name='crm_lead_loja_conta_idx'),
        ]

    def __str__(self):
        return f"{self.nome} ({self.empresa or '-'})"


class Contato(LojaIsolationMixin, models.Model):
    """Contato (pessoa) vinculado a uma conta."""
    nome = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True)
    cargo = models.CharField(max_length=100, blank=True)
    conta = models.ForeignKey(
        Conta,
        on_delete=models.CASCADE,
        related_name='contatos',
    )
    observacoes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_vendas_contato'
        ordering = ['nome']
        verbose_name = 'Contato'
        verbose_name_plural = 'Contatos'
        indexes = [
            models.Index(fields=['loja_id', 'conta'], name='crm_contato_loja_conta_idx'),
            models.Index(fields=['loja_id', 'email'], name='crm_contato_loja_email_idx'),
        ]

    def __str__(self):
        return self.nome


class Oportunidade(LojaIsolationMixin, models.Model):
    """Oportunidade (deal) no pipeline de vendas."""
    ETAPA_CHOICES = [
        ('prospecting', 'Prospecção'),
        ('qualification', 'Qualificação'),
        ('proposal', 'Proposta'),
        ('negotiation', 'Negociação'),
        ('closed_won', 'Fechado ganho'),
        ('closed_lost', 'Fechado perdido'),
    ]

    titulo = models.CharField(max_length=255)
    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='oportunidades',
    )
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    etapa = models.CharField(max_length=50, choices=ETAPA_CHOICES, default='prospecting')
    vendedor = models.ForeignKey(
        Vendedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='oportunidades',
    )
    probabilidade = models.IntegerField(default=50)  # 0-100
    data_fechamento_prevista = models.DateField(null=True, blank=True)
    data_fechamento = models.DateField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_vendas_oportunidade'
        ordering = ['-created_at']
        verbose_name = 'Oportunidade'
        verbose_name_plural = 'Oportunidades'
        indexes = [
            models.Index(fields=['loja_id', 'etapa'], name='crm_opor_loja_etapa_idx'),
            models.Index(fields=['loja_id', 'vendedor'], name='crm_opor_loja_vend_idx'),
            models.Index(fields=['loja_id', 'lead'], name='crm_opor_loja_lead_idx'),
            models.Index(fields=['loja_id', 'data_fechamento'], name='crm_opor_loja_dtfech_idx'),
            models.Index(fields=['loja_id', 'etapa', 'vendedor'], name='crm_opor_loja_etapa_vend_idx'),
            models.Index(fields=['loja_id', 'created_at'], name='crm_opor_loja_created_idx'),
        ]

    def __str__(self):
        return f"{self.titulo} - R$ {self.valor}"


class Atividade(LojaIsolationMixin, models.Model):
    """Atividade (tarefa, ligação, reunião, email)."""
    TIPO_CHOICES = [
        ('call', 'Ligação'),
        ('meeting', 'Reunião'),
        ('email', 'Email'),
        ('task', 'Tarefa'),
    ]

    titulo = models.CharField(max_length=255)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default='task')
    oportunidade = models.ForeignKey(
        Oportunidade,
        on_delete=models.CASCADE,
        related_name='atividades',
        null=True,
        blank=True,
    )
    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='atividades',
        null=True,
        blank=True,
    )
    data = models.DateTimeField()
    duracao_minutos = models.PositiveIntegerField(
        default=60,
        help_text='Duração estimada da atividade em minutos'
    )
    concluido = models.BooleanField(default=False)
    observacoes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    google_event_id = models.CharField(max_length=255, blank=True, null=True, help_text='ID do evento no Google Calendar (sincronização)')

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_vendas_atividade'
        ordering = ['data']
        verbose_name = 'Atividade'
        verbose_name_plural = 'Atividades'
        indexes = [
            models.Index(fields=['loja_id', 'data'], name='crm_ativ_loja_data_idx'),
            models.Index(fields=['loja_id', 'concluido'], name='crm_ativ_loja_concl_idx'),
            models.Index(fields=['loja_id', 'oportunidade'], name='crm_ativ_loja_opor_idx'),
            models.Index(fields=['loja_id', 'lead'], name='crm_ativ_loja_lead_idx'),
            models.Index(fields=['loja_id', 'data', 'concluido'], name='crm_ativ_loja_data_concl_idx'),
        ]

    def __str__(self):
        return f"{self.titulo} ({self.get_tipo_display()})"
