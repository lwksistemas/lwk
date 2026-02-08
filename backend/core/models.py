"""
Modelos base abstratos para evitar duplicação de código
"""
from django.db import models


class BaseModel(models.Model):
    """
    Modelo base abstrato com campos comuns a todos os modelos
    """
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        abstract = True


class BaseCategoria(BaseModel):
    """
    Modelo base abstrato para categorias
    Usado em: servicos, restaurante, ecommerce
    """
    nome = models.CharField(max_length=100, verbose_name="Nome")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    
    class Meta:
        abstract = True
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class BaseCliente(BaseModel):
    """
    Modelo base abstrato para clientes
    Usado em: servicos, restaurante, ecommerce, crm_vendas
    """
    nome = models.CharField(max_length=200, verbose_name="Nome")
    email = models.EmailField(blank=True, null=True, verbose_name="E-mail")
    telefone = models.CharField(max_length=20, verbose_name="Telefone")
    cpf_cnpj = models.CharField(max_length=18, blank=True, null=True, verbose_name="CPF/CNPJ")
    
    # Endereço
    cep = models.CharField(max_length=9, blank=True, null=True, verbose_name="CEP")
    endereco = models.CharField(max_length=200, blank=True, null=True, verbose_name="Endereço")
    numero = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número")
    complemento = models.CharField(max_length=100, blank=True, null=True, verbose_name="Complemento")
    bairro = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bairro")
    cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade")
    estado = models.CharField(max_length=2, blank=True, null=True, verbose_name="Estado")
    
    class Meta:
        abstract = True
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class BasePedido(BaseModel):
    """
    Modelo base abstrato para pedidos
    Usado em: restaurante, ecommerce
    """
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('confirmado', 'Confirmado'),
        ('preparando', 'Preparando'),
        ('pronto', 'Pronto'),
        ('entregue', 'Entregue'),
        ('cancelado', 'Cancelado'),
    ]
    
    numero_pedido = models.CharField(max_length=20, unique=True, verbose_name="Número do Pedido")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente', verbose_name="Status")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Subtotal")
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Desconto")
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Pedido {self.numero_pedido}"


class BaseItemPedido(BaseModel):
    """
    Modelo base abstrato para itens de pedido
    Usado em: restaurante, ecommerce
    """
    quantidade = models.IntegerField(verbose_name="Quantidade")
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço Unitário")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Subtotal")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """Calcula o subtotal automaticamente"""
        self.subtotal = self.quantidade * self.preco_unitario
        super().save(*args, **kwargs)


class BaseFuncionario(BaseModel):
    """
    Modelo base abstrato para funcionários
    Usado em: servicos, restaurante
    """
    nome = models.CharField(max_length=200, verbose_name="Nome")
    email = models.EmailField(blank=True, null=True, verbose_name="E-mail")
    telefone = models.CharField(max_length=20, verbose_name="Telefone")
    cargo = models.CharField(max_length=100, verbose_name="Cargo")
    is_admin = models.BooleanField(default=False, verbose_name="É Administrador", help_text='Indica se é o administrador da loja')
    
    class Meta:
        abstract = True
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} - {self.cargo}"


class BaseProduto(BaseModel):
    """
    Modelo base abstrato para produtos
    Usado em: ecommerce, crm_vendas
    """
    nome = models.CharField(max_length=200, verbose_name="Nome")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    preco = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço")
    estoque = models.IntegerField(default=0, verbose_name="Estoque")
    codigo = models.CharField(max_length=50, blank=True, null=True, verbose_name="Código")
    
    class Meta:
        abstract = True
        ordering = ['nome']
    
    def __str__(self):
        return self.nome



class HistoricoAcao(BaseModel):
    """
    Modelo base para histórico de ações dos usuários
    Registra login, logout e ações realizadas no sistema
    Reutilizável por todos os tipos de loja
    """
    ACAO_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('criar', 'Criar'),
        ('editar', 'Editar'),
        ('excluir', 'Excluir'),
        ('visualizar', 'Visualizar'),
        ('exportar', 'Exportar'),
        ('importar', 'Importar'),
    ]
    
    # Informações do usuário
    usuario = models.CharField(max_length=200, verbose_name="Usuário")
    usuario_nome = models.CharField(max_length=200, verbose_name="Nome do Usuário")
    
    # Informações da ação
    acao = models.CharField(max_length=20, choices=ACAO_CHOICES, verbose_name="Ação")
    detalhes = models.TextField(blank=True, null=True, verbose_name="Detalhes")
    
    # Informações técnicas
    ip_address = models.GenericIPAddressField(verbose_name="Endereço IP")
    user_agent = models.TextField(blank=True, null=True, verbose_name="User Agent")
    
    # Loja (para isolamento multi-tenant)
    loja_id = models.IntegerField(verbose_name="ID da Loja")
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
        verbose_name = 'Histórico de Ação'
        verbose_name_plural = 'Histórico de Ações'
        indexes = [
            models.Index(fields=['loja_id', '-created_at']),
            models.Index(fields=['usuario', '-created_at']),
            models.Index(fields=['acao', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.usuario_nome} - {self.acao} - {self.created_at}"
