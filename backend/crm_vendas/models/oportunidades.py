from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin

from .contas import Conta
from .leads import Lead
from .vendedores import Vendedor


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
    empresa_prestadora = models.ForeignKey(
        Conta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='oportunidades_prestadas',
        help_text='Empresa para a qual o serviço é prestado nesta oportunidade',
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
    data_fechamento_ganho = models.DateField(null=True, blank=True, help_text='Data em que a oportunidade foi fechada como ganha')
    data_fechamento_perdido = models.DateField(null=True, blank=True, help_text='Data em que a oportunidade foi fechada como perdida')
    valor_comissao = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Valor da comissão para esta oportunidade')
    observacoes = models.TextField(blank=True)
    motivo_perda = models.TextField(
        blank=True,
        default='',
        help_text='Motivo pelo qual a negociação foi perdida ou cancelada',
    )
    feedback_pos_venda = models.TextField(
        blank=True,
        default='',
        help_text='Opinião do cliente após fechamento ganho (sobre o serviço/sistema)',
    )
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
            models.Index(fields=['loja_id', 'data_fechamento_ganho'], name='crm_opor_loja_dtfechganho_idx'),
            models.Index(fields=['loja_id', 'data_fechamento_perdido'], name='crm_opor_loja_dtfechperd_idx'),
            models.Index(fields=['loja_id', 'etapa', 'vendedor'], name='crm_opor_loja_etapa_vend_idx'),
            models.Index(fields=['loja_id', 'created_at'], name='crm_opor_loja_created_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(probabilidade__gte=0) & models.Q(probabilidade__lte=100),
                name='crm_opor_prob_range',
            ),
        ]

    def __str__(self):
        return f"{self.titulo} - R$ {self.valor}"

