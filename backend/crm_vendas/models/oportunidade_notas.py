from django.db import models

from core.mixins import LojaIsolationMixin, LojaIsolationManager

from .oportunidades import Oportunidade


class OportunidadeNota(LojaIsolationMixin, models.Model):
    """Registro cronológico da negociação (respostas do cliente e notas internas)."""

    TIPO_CHOICES = [
        ('resposta_cliente', 'Resposta do cliente'),
        ('nota_interna', 'Nota interna'),
    ]

    oportunidade = models.ForeignKey(
        Oportunidade,
        on_delete=models.CASCADE,
        related_name='notas_negociacao',
    )
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, default='resposta_cliente')
    texto = models.TextField()
    autor_nome = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_vendas_oportunidade_nota'
        ordering = ['created_at']
        verbose_name = 'Nota de negociação'
        verbose_name_plural = 'Notas de negociação'
        indexes = [
            models.Index(fields=['loja_id', 'oportunidade'], name='crm_opor_nota_loja_op_idx'),
            models.Index(fields=['loja_id', 'created_at'], name='crm_opor_nota_loja_dt_idx'),
        ]

    def __str__(self):
        return f'Nota #{self.id} — {self.get_tipo_display()}'
