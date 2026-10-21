from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin

from .catalogo import ProdutoServico
from .contas import Conta


class ContaProdutoComissao(LojaIsolationMixin, models.Model):
    """Valor que a empresa prestadora paga à loja por um produto ou serviço."""

    conta = models.ForeignKey(
        Conta,
        on_delete=models.CASCADE,
        related_name="comissoes_produtos",
    )
    produto_servico = models.ForeignKey(
        ProdutoServico,
        on_delete=models.CASCADE,
        related_name="comissoes_prestadoras",
    )
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Valor em reais que a prestadora paga à loja por este item",
    )

    objects = LojaIsolationManager()

    class Meta:
        db_table = "crm_vendas_conta_produto_comissao"
        verbose_name = "Comissão da prestadora"
        verbose_name_plural = "Comissões da prestadora"
        constraints = [
            models.UniqueConstraint(
                fields=["conta", "produto_servico"],
                name="crm_conta_prod_comissao_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["loja_id", "conta"], name="crm_cpc_loja_conta_idx"),
        ]

    def __str__(self):
        return f"{self.conta_id} · {self.produto_servico_id} · {self.valor}"
