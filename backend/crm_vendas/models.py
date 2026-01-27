from django.db import models
from core.models import BaseCliente, BaseFuncionario, BaseProduto
from core.mixins import LojaIsolationMixin, LojaIsolationManager


class Lead(LojaIsolationMixin, models.Model):
    """Leads do CRM"""
    STATUS_CHOICES = [
        ('novo', 'Novo Lead'),
        ('contato_inicial', 'Contato Inicial'),
        ('qualificado', 'Qualificado'),
        ('proposta_enviada', 'Proposta Enviada'),
        ('negociacao', 'Negociação'),
        ('fechado', 'Fechado'),
        ('perdido', 'Perdido'),
    ]

    ORIGEM_CHOICES = [
        ('site', 'Site'),
        ('indicacao', 'Indicação'),
        ('redes_sociais', 'Redes Sociais'),
        ('email_marketing', 'Email Marketing'),
        ('evento', 'Evento'),
        ('telefone', 'Telefone'),
        ('outro', 'Outro'),
    ]

    nome = models.CharField(max_length=200)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    empresa = models.CharField(max_length=200)
    cargo = models.CharField(max_length=100, blank=True, null=True)
    origem = models.CharField(max_length=50, choices=ORIGEM_CHOICES)
    interesse = models.CharField(max_length=200)
    valor_estimado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='novo')
    observacoes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_leads'
        ordering = ['-created_at']
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'

    def __str__(self):
        return f"{self.nome} - {self.empresa}"


class Cliente(LojaIsolationMixin, BaseCliente):
    """Clientes do CRM (leads convertidos)"""
    empresa = models.CharField(max_length=200)
    cnpj = models.CharField(max_length=18, blank=True, null=True)
    
    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_clientes'
        ordering = ['-created_at']
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return f"{self.nome} - {self.empresa}"


class Vendedor(LojaIsolationMixin, BaseFuncionario):
    """Vendedores da equipe"""
    meta_mensal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_vendedores'
        ordering = ['nome']
        verbose_name = 'Vendedor'
        verbose_name_plural = 'Vendedores'


class Produto(LojaIsolationMixin, BaseProduto):
    """Produtos/Serviços oferecidos"""
    categoria = models.CharField(max_length=100)
    
    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_produtos'
        ordering = ['categoria', 'nome']
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'


class Venda(LojaIsolationMixin, models.Model):
    """Vendas realizadas"""
    STATUS_CHOICES = [
        ('em_negociacao', 'Em Negociação'),
        ('fechada', 'Fechada'),
        ('cancelada', 'Cancelada'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='vendas')
    vendedor = models.ForeignKey(Vendedor, on_delete=models.SET_NULL, null=True, related_name='vendas')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='vendas')
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='em_negociacao')
    data_fechamento = models.DateField(blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_vendas'
        ordering = ['-created_at']
        verbose_name = 'Venda'
        verbose_name_plural = 'Vendas'

    def __str__(self):
        return f"{self.cliente.nome} - {self.produto.nome} - R$ {self.valor}"


class Pipeline(LojaIsolationMixin, models.Model):
    """Etapas do pipeline de vendas"""
    nome = models.CharField(max_length=100)
    ordem = models.IntegerField()
    cor = models.CharField(max_length=7, default='#3B82F6')  # Hex color
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = LojaIsolationManager()

    class Meta:
        db_table = 'crm_pipeline'
        ordering = ['ordem']
        verbose_name = 'Etapa do Pipeline'
        verbose_name_plural = 'Etapas do Pipeline'

    def __str__(self):
        return self.nome
