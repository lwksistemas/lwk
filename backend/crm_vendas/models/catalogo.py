from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin

from ..managers import ProdutoServicoManager


class CategoriaProdutoServico(LojaIsolationMixin, models.Model):
    """Categoria para organizar produtos e serviços em grupos."""

    nome = models.CharField(max_length=100, help_text="Nome da categoria (ex: Hardware, Software, Consultoria)")
    descricao = models.TextField(blank=True, help_text="Descrição da categoria")
    cor = models.CharField(max_length=7, default="#3B82F6", help_text="Cor para identificação visual (hex)")
    ordem = models.IntegerField(default=0, help_text="Ordem de exibição")
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = "crm_vendas_categoria_produto_servico"
        ordering = ["ordem", "nome"]
        verbose_name = "Categoria de Produto/Serviço"
        verbose_name_plural = "Categorias de Produtos/Serviços"
        indexes = [
            models.Index(fields=["loja_id", "ativo"], name="crm_cat_ps_loja_ativo_idx"),
            models.Index(fields=["loja_id", "ordem"], name="crm_cat_ps_loja_ordem_idx"),
        ]

    def __str__(self):
        return self.nome


class ProdutoServico(LojaIsolationMixin, models.Model):
    """Produto ou serviço cadastrado para uso em oportunidades e propostas."""

    TIPO_CHOICES = [
        ("produto", "Produto"),
        ("servico", "Serviço"),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="produto")
    codigo = models.CharField(
        max_length=50,
        blank=True,
        help_text="Código interno único (ex: PROD-001, SERV-CONS-01)",
    )
    nome = models.CharField(max_length=255)
    descricao = models.TextField(blank=True)
    categoria = models.ForeignKey(
        CategoriaProdutoServico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="produtos_servicos",
        help_text="Categoria/Grupo do produto ou serviço",
    )
    preco = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    RECORRENCIA_CHOICES = [
        ("unico", "Único (adesão/implantação)"),
        ("mensal", "Mensal"),
        ("trimestral", "Trimestral"),
        ("anual", "Anual"),
    ]
    recorrencia = models.CharField(
        max_length=20, choices=RECORRENCIA_CHOICES, default="unico",
        help_text="Tipo de cobrança: único (adesão) ou recorrente (mensal, trimestral, anual)",
    )
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProdutoServicoManager()

    class Meta:
        db_table = "crm_vendas_produto_servico"
        ordering = ["categoria__ordem", "categoria__nome", "codigo", "nome"]
        verbose_name = "Produto/Serviço"
        verbose_name_plural = "Produtos e Serviços"
        indexes = [
            models.Index(fields=["loja_id", "tipo"], name="crm_ps_loja_tipo_idx"),
            models.Index(fields=["loja_id", "ativo"], name="crm_ps_loja_ativo_idx"),
            models.Index(fields=["loja_id", "categoria"], name="crm_ps_loja_cat_idx"),
            models.Index(fields=["loja_id", "codigo"], name="crm_ps_loja_codigo_idx"),
        ]
        # Garantir que o código seja único dentro da loja
        constraints = [
            models.UniqueConstraint(
                fields=["loja_id", "codigo"],
                name="crm_ps_unique_codigo_loja",
                condition=models.Q(codigo__isnull=False) & ~models.Q(codigo=""),
            ),
        ]

    def __str__(self):
        if self.codigo:
            return f"[{self.codigo}] {self.nome}"
        return f"{self.get_tipo_display()}: {self.nome}"

    def save(self, *args, **kwargs):
        """Gera código automático se não fornecido usando o Manager."""
        if not self.codigo:
            self.codigo = self.__class__.objects.gerar_proximo_codigo(
                self.tipo,
                self.loja_id,
            )
        super().save(*args, **kwargs)
