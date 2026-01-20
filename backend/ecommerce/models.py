from django.db import models
from django.contrib.auth.models import User
from core.models import BaseCategoria, BaseCliente, BasePedido, BaseItemPedido, BaseProduto


class Categoria(BaseCategoria):
    """Categorias de produtos"""

    class Meta:
        db_table = 'ecommerce_categorias'
        ordering = ['nome']
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'


class Produto(BaseProduto):
    """Produtos do e-commerce"""
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, related_name='produtos')
    preco_promocional = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    sku = models.CharField(max_length=50, unique=True)
    peso = models.DecimalField(max_digits=8, decimal_places=3, blank=True, null=True, help_text='Peso em kg')
    largura = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, help_text='Largura em cm')
    altura = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, help_text='Altura em cm')
    comprimento = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, help_text='Comprimento em cm')
    imagem_url = models.URLField(blank=True, null=True)

    class Meta:
        db_table = 'ecommerce_produtos'
        ordering = ['-created_at']
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'


class Cliente(BaseCliente):
    """Clientes do e-commerce"""
    data_nascimento = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'ecommerce_clientes'
        ordering = ['-created_at']
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'


class Pedido(BasePedido):
    """Pedidos do e-commerce"""
    PAGAMENTO_CHOICES = [
        ('pix', 'PIX'),
        ('cartao_credito', 'Cartão de Crédito'),
        ('cartao_debito', 'Cartão de Débito'),
        ('boleto', 'Boleto'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='pedidos')
    forma_pagamento = models.CharField(max_length=20, choices=PAGAMENTO_CHOICES)
    frete = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    codigo_rastreio = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'ecommerce_pedidos'
        ordering = ['-created_at']
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'

    def __str__(self):
        return f"Pedido #{self.numero_pedido} - {self.cliente.nome}"


class ItemPedido(BaseItemPedido):
    """Itens do pedido"""
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)

    class Meta:
        db_table = 'ecommerce_itens_pedido'
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens do Pedido'

    def __str__(self):
        return f"{self.produto.nome} x{self.quantidade}"


class Cupom(models.Model):
    """Cupons de desconto"""
    TIPO_CHOICES = [
        ('percentual', 'Percentual'),
        ('valor_fixo', 'Valor Fixo'),
    ]

    codigo = models.CharField(max_length=50, unique=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    valor_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantidade_disponivel = models.IntegerField(default=1)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ecommerce_cupons'
        ordering = ['-created_at']
        verbose_name = 'Cupom'
        verbose_name_plural = 'Cupons'

    def __str__(self):
        return self.codigo
