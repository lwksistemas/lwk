from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin

from .catalogo import ProdutoServico
from .oportunidades import Oportunidade


class OportunidadeItem(LojaIsolationMixin, models.Model):
    """Item (produto/serviço) vinculado a uma oportunidade."""
    oportunidade = models.ForeignKey(
        Oportunidade,
        on_delete=models.CASCADE,
        related_name='itens',
    )
    produto_servico = models.ForeignKey(
        ProdutoServico,
        on_delete=models.CASCADE,
        related_name='oportunidade_itens',
    )
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    preco_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    observacao = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_vendas_oportunidade_item'
        ordering = ['id']
        verbose_name = 'Item da Oportunidade'
        verbose_name_plural = 'Itens da Oportunidade'
        indexes = [
            models.Index(fields=['loja_id', 'oportunidade'], name='crm_oi_loja_opor_idx'),
        ]

    @property
    def subtotal(self):
        return self.quantidade * self.preco_unitario

