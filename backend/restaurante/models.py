from django.db import models
from django.contrib.auth.models import User


class Categoria(models.Model):
    """Categorias do cardápio"""
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    ordem = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'restaurante_categorias'
        ordering = ['ordem', 'nome']
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'

    def __str__(self):
        return self.nome


class ItemCardapio(models.Model):
    """Itens do cardápio"""
    nome = models.CharField(max_length=200)
    descricao = models.TextField()
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, related_name='itens')
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    tempo_preparo = models.IntegerField(help_text='Tempo em minutos')
    imagem_url = models.URLField(blank=True, null=True)
    ingredientes = models.TextField(blank=True, null=True)
    calorias = models.IntegerField(blank=True, null=True)
    is_disponivel = models.BooleanField(default=True)
    is_destaque = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'restaurante_cardapio'
        ordering = ['categoria', 'nome']
        verbose_name = 'Item do Cardápio'
        verbose_name_plural = 'Itens do Cardápio'

    def __str__(self):
        return f"{self.nome} - R$ {self.preco}"


class Mesa(models.Model):
    """Mesas do restaurante"""
    STATUS_CHOICES = [
        ('livre', 'Livre'),
        ('ocupada', 'Ocupada'),
        ('reservada', 'Reservada'),
        ('manutencao', 'Manutenção'),
    ]

    numero = models.CharField(max_length=10, unique=True)
    capacidade = models.IntegerField()
    localizacao = models.CharField(max_length=100, blank=True, null=True, help_text='Ex: Salão, Varanda, etc')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='livre')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'restaurante_mesas'
        ordering = ['numero']
        verbose_name = 'Mesa'
        verbose_name_plural = 'Mesas'

    def __str__(self):
        return f"Mesa {self.numero} ({self.capacidade} pessoas)"


class Cliente(models.Model):
    """Clientes do restaurante"""
    nome = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20)
    cpf = models.CharField(max_length=14, blank=True, null=True)
    data_nascimento = models.DateField(blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True, help_text='Preferências, restrições alimentares, etc')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'restaurante_clientes'
        ordering = ['-created_at']
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return self.nome


class Reserva(models.Model):
    """Reservas de mesas"""
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('confirmada', 'Confirmada'),
        ('em_andamento', 'Em Andamento'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='reservas')
    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE, related_name='reservas')
    data = models.DateField()
    horario = models.TimeField()
    quantidade_pessoas = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    observacoes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'restaurante_reservas'
        ordering = ['data', 'horario']
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'

    def __str__(self):
        return f"Reserva {self.cliente.nome} - Mesa {self.mesa.numero} - {self.data} {self.horario}"


class Pedido(models.Model):
    """Pedidos do restaurante"""
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_preparo', 'Em Preparo'),
        ('pronto', 'Pronto'),
        ('entregue', 'Entregue'),
        ('cancelado', 'Cancelado'),
    ]

    TIPO_CHOICES = [
        ('local', 'Local'),
        ('delivery', 'Delivery'),
        ('retirada', 'Retirada'),
    ]

    numero_pedido = models.CharField(max_length=20, unique=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='pedidos', blank=True, null=True)
    mesa = models.ForeignKey(Mesa, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    taxa_servico = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    taxa_entrega = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    observacoes = models.TextField(blank=True, null=True)
    endereco_entrega = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'restaurante_pedidos'
        ordering = ['-created_at']
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'

    def __str__(self):
        return f"Pedido #{self.numero_pedido}"


class ItemPedido(models.Model):
    """Itens do pedido"""
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens')
    item_cardapio = models.ForeignKey(ItemCardapio, on_delete=models.CASCADE)
    quantidade = models.IntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    observacoes = models.TextField(blank=True, null=True, help_text='Ex: sem cebola, ponto da carne, etc')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'restaurante_itens_pedido'
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens do Pedido'

    def __str__(self):
        return f"{self.item_cardapio.nome} x{self.quantidade}"


class Funcionario(models.Model):
    """Funcionários do restaurante"""
    CARGO_CHOICES = [
        ('garcom', 'Garçom'),
        ('cozinheiro', 'Cozinheiro'),
        ('gerente', 'Gerente'),
        ('caixa', 'Caixa'),
        ('outro', 'Outro'),
    ]

    nome = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20)
    cargo = models.CharField(max_length=20, choices=CARGO_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'restaurante_funcionarios'
        ordering = ['nome']
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'

    def __str__(self):
        return f"{self.nome} - {self.get_cargo_display()}"
