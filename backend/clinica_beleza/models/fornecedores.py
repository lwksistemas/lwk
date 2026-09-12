"""Fornecedores, catálogo de produtos e pedidos de compra (não dão entrada no estoque)."""
from decimal import Decimal

from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin


class Fornecedor(LojaIsolationMixin, models.Model):
    cnpj = models.CharField(max_length=18, verbose_name="CNPJ")
    razao_social = models.CharField(max_length=200, verbose_name="Razão social")
    nome_fantasia = models.CharField(max_length=200, blank=True, default="", verbose_name="Nome fantasia")
    inscricao_estadual = models.CharField(max_length=30, blank=True, default="", verbose_name="IE")
    email = models.EmailField(blank=True, default="", verbose_name="E-mail")
    telefone = models.CharField(max_length=20, blank=True, default="", verbose_name="Telefone")
    cep = models.CharField(max_length=10, blank=True, default="")
    logradouro = models.CharField(max_length=200, blank=True, default="")
    numero = models.CharField(max_length=20, blank=True, default="")
    complemento = models.CharField(max_length=100, blank=True, default="")
    bairro = models.CharField(max_length=100, blank=True, default="")
    municipio = models.CharField(max_length=100, blank=True, default="")
    uf = models.CharField(max_length=2, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        db_table = "clinica_beleza_fornecedor"
        ordering = ["razao_social"]
        indexes = [
            models.Index(fields=["loja_id", "cnpj"], name="cb_forn_loja_cnpj_idx"),
        ]

    def __str__(self):
        return self.nome_fantasia or self.razao_social


class FornecedorProduto(LojaIsolationMixin, models.Model):
    """Catálogo do fornecedor — usado só para montar o pedido."""

    fornecedor = models.ForeignKey(
        Fornecedor, on_delete=models.CASCADE, related_name="produtos",
    )
    codigo = models.CharField(max_length=60, verbose_name="Código")
    nome = models.CharField(max_length=200, verbose_name="Nome")
    unidade = models.CharField(max_length=20, blank=True, default="un")
    preco_ref = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="Preço ref.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        db_table = "clinica_beleza_fornecedor_produto"
        ordering = ["nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["fornecedor", "codigo"],
                name="cb_forn_prod_codigo_uniq",
            ),
        ]

    def __str__(self):
        return f"{self.codigo} — {self.nome}"


class PedidoCompra(LojaIsolationMixin, models.Model):
    STATUS_RASCUNHO = "rascunho"
    STATUS_AGUARDANDO_FORNECEDOR = "aguardando_fornecedor"
    STATUS_ASSINADO = "assinado"
    STATUS_ENVIADO = "enviado"
    STATUS_CANCELADO = "cancelado"
    STATUS_CHOICES = (
        (STATUS_RASCUNHO, "Rascunho"),
        (STATUS_AGUARDANDO_FORNECEDOR, "Aguardando fornecedor"),
        (STATUS_ASSINADO, "Assinado"),
        (STATUS_ENVIADO, "Enviado"),
        (STATUS_CANCELADO, "Cancelado"),
    )

    numero = models.PositiveIntegerField(verbose_name="Número")
    fornecedor = models.ForeignKey(
        Fornecedor, on_delete=models.PROTECT, related_name="pedidos",
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_RASCUNHO)
    observacoes = models.TextField(blank=True, default="")
    pdf_url = models.URLField(max_length=500, blank=True, default="")
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        db_table = "clinica_beleza_pedido_compra"
        ordering = ["-numero"]
        constraints = [
            models.UniqueConstraint(fields=["loja_id", "numero"], name="cb_pedido_loja_num_uniq"),
        ]

    def __str__(self):
        return f"Pedido #{self.numero}"


class PedidoCompraItem(models.Model):
    pedido = models.ForeignKey(PedidoCompra, on_delete=models.CASCADE, related_name="itens")
    catalogo = models.ForeignKey(
        FornecedorProduto, on_delete=models.SET_NULL, null=True, blank=True,
    )
    codigo = models.CharField(max_length=60)
    nome = models.CharField(max_length=200)
    unidade = models.CharField(max_length=20, blank=True, default="un")
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1"))
    preco = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        app_label = "clinica_beleza"
        db_table = "clinica_beleza_pedido_compra_item"
        ordering = ["id"]

    @property
    def subtotal(self):
        return self.quantidade * self.preco


class PedidoCompraAssinatura(LojaIsolationMixin, models.Model):
    TIPO_CLINICA = "clinica"
    TIPO_FORNECEDOR = "fornecedor"
    TIPO_CHOICES = (
        (TIPO_CLINICA, "Clínica"),
        (TIPO_FORNECEDOR, "Fornecedor"),
    )

    pedido = models.ForeignKey(
        PedidoCompra, on_delete=models.CASCADE, related_name="assinaturas",
    )
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    profissional = models.ForeignKey(
        "clinica_beleza.Professional",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assinaturas_pedido_compra",
    )
    nome_assinante = models.CharField(max_length=200, blank=True, default="")
    conselho_display = models.CharField(max_length=80, blank=True, default="")
    cpf_assinante = models.CharField(max_length=14, blank=True, default="")
    email_assinante = models.EmailField(blank=True, default="")
    ip_address = models.GenericIPAddressField(default="0.0.0.0")
    token = models.CharField(max_length=512, blank=True, default="", db_index=True)
    assinado = models.BooleanField(default=False)
    assinado_em = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        db_table = "clinica_beleza_pedido_assinatura"
        indexes = [
            models.Index(fields=["pedido", "tipo"], name="cb_pedido_ass_tipo_idx"),
        ]
