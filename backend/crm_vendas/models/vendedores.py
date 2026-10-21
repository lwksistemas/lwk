from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin


class Vendedor(LojaIsolationMixin, models.Model):
    """Vendedor da loja (equipe de vendas)."""

    nome = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True)
    cargo = models.CharField(max_length=100, default="Vendedor")
    comissao_padrao = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Porcentagem de comissão padrão (ex: 5.00 para 5%)",
    )
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    config_acesso = models.JSONField(
        default=dict,
        blank=True,
        help_text="Configuração de grupo/permissões (grupo_id, permissoes_ids) para acesso ao CRM",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = "crm_vendas_vendedor"
        ordering = ["nome"]
        verbose_name = "Vendedor"
        verbose_name_plural = "Vendedores"
        indexes = [
            models.Index(fields=["loja_id", "is_active"], name="crm_vend_loja_active_idx"),
            models.Index(fields=["loja_id", "email"], name="crm_vend_loja_email_idx"),
        ]

    def __str__(self):
        return self.nome


class VendedorCategoriaComissao(LojaIsolationMixin, models.Model):
    """Comissão do vendedor em uma categoria: valor fixo ou porcentagem."""

    TIPO_FIXO = "fixo"
    TIPO_PERCENTUAL = "percentual"
    TIPO_CHOICES = [
        (TIPO_FIXO, "Valor fixo"),
        (TIPO_PERCENTUAL, "Porcentagem"),
    ]

    vendedor = models.ForeignKey(
        Vendedor,
        on_delete=models.CASCADE,
        related_name="comissoes_categoria",
    )
    categoria = models.ForeignKey(
        "crm_vendas.CategoriaProdutoServico",
        on_delete=models.CASCADE,
        related_name="comissoes_vendedores",
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=TIPO_PERCENTUAL)
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Reais por unidade, quando o tipo é valor fixo. Percentual, quando o tipo é porcentagem.",
    )

    objects = LojaIsolationManager()

    class Meta:
        db_table = "crm_vendas_vendedor_categoria_comissao"
        verbose_name = "Comissão do vendedor por categoria"
        verbose_name_plural = "Comissões do vendedor por categoria"
        constraints = [
            models.UniqueConstraint(
                fields=["vendedor", "categoria"],
                name="crm_vend_cat_comissao_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["loja_id", "vendedor"], name="crm_vcc_loja_vend_idx"),
        ]

    def __str__(self):
        return f"{self.vendedor_id} · {self.categoria_id} · {self.tipo} {self.valor}"

