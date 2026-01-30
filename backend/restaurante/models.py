from django.db import models
from core.models import BaseCategoria, BaseCliente, BasePedido, BaseItemPedido, BaseFuncionario
from core.mixins import LojaIsolationMixin, LojaIsolationManager


class Categoria(BaseCategoria):
    """Categorias do cardápio"""
    ordem = models.IntegerField(default=0)

    class Meta:
        db_table = 'restaurante_categorias'
        ordering = ['ordem', 'nome']
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'


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


class Cliente(BaseCliente):
    """Clientes do restaurante"""
    data_nascimento = models.DateField(blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True, help_text='Preferências, restrições alimentares, etc')

    class Meta:
        db_table = 'restaurante_clientes'
        ordering = ['-created_at']
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'


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


class Pedido(BasePedido):
    """Pedidos do restaurante"""
    TIPO_CHOICES = [
        ('local', 'Local'),
        ('delivery', 'Delivery'),
        ('retirada', 'Retirada'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='pedidos', blank=True, null=True)
    mesa = models.ForeignKey(Mesa, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    
    taxa_servico = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    taxa_entrega = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    endereco_entrega = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'restaurante_pedidos'
        ordering = ['-created_at']
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'


class ItemPedido(BaseItemPedido):
    """Itens do pedido"""
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens')
    item_cardapio = models.ForeignKey(ItemCardapio, on_delete=models.CASCADE)

    class Meta:
        db_table = 'restaurante_itens_pedido'
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens do Pedido'

    def __str__(self):
        return f"{self.item_cardapio.nome} x{self.quantidade}"


class Funcionario(LojaIsolationMixin, BaseFuncionario):
    """Funcionários do restaurante (isolados por loja)."""
    CARGO_CHOICES = [
        ('garcom', 'Garçom'),
        ('cozinheiro', 'Cozinheiro'),
        ('gerente', 'Gerente'),
        ('caixa', 'Caixa'),
        ('outro', 'Outro'),
    ]

    cargo = models.CharField(max_length=20, choices=CARGO_CHOICES)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'restaurante_funcionarios'
        ordering = ['nome']
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'

    def __str__(self):
        return f"{self.nome} - {self.get_cargo_display()}"


class Fornecedor(LojaIsolationMixin, models.Model):
    """Fornecedores do restaurante (compras / NF de entrada)."""
    nome = models.CharField(max_length=200, verbose_name='Nome/Razão Social')
    cnpj = models.CharField(max_length=18, blank=True, null=True, verbose_name='CNPJ')
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    endereco = models.TextField(blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'restaurante_fornecedores'
        ordering = ['nome']
        verbose_name = 'Fornecedor'
        verbose_name_plural = 'Fornecedores'

    def __str__(self):
        return self.nome


def nfe_upload_path(instance, filename):
    """Ex: nfe_restaurante/2025/01/loja_1_<unique>_<filename>"""
    import uuid
    from django.utils import timezone
    safe = (instance.numero or str(instance.id or uuid.uuid4().hex[:8])).replace(' ', '_')
    return f"nfe_restaurante/{timezone.now().strftime('%Y/%m')}/loja_{getattr(instance, 'loja_id', 0)}_{safe}_{filename}"


class NotaFiscalEntrada(LojaIsolationMixin, models.Model):
    """Entrada de nota fiscal de compra (NF-e) vinculada a fornecedor e opcionalmente ao estoque."""
    numero = models.CharField(max_length=30, verbose_name='Número da NF')
    fornecedor = models.ForeignKey(
        Fornecedor, on_delete=models.PROTECT, related_name='notas_fiscais',
        verbose_name='Fornecedor'
    )
    data_emissao = models.DateField(verbose_name='Data de emissão', null=True, blank=True)
    data_entrada = models.DateField(verbose_name='Data de entrada', null=True, blank=True)
    valor_total = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Valor total'
    )
    xml_file = models.FileField(
        upload_to=nfe_upload_path, blank=True, null=True,
        verbose_name='Arquivo XML da NF-e'
    )
    observacoes = models.TextField(blank=True, null=True)
    aplicado_estoque = models.BooleanField(
        default=False,
        verbose_name='Aplicado ao estoque',
        help_text='Se os itens da NF já foram lançados no estoque'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'restaurante_notas_fiscais_entrada'
        ordering = ['-data_entrada', '-created_at']
        verbose_name = 'Nota Fiscal de Entrada'
        verbose_name_plural = 'Notas Fiscais de Entrada'

    def __str__(self):
        return f"NF {self.numero} - {self.fornecedor.nome}"


class ItemNotaFiscalEntrada(models.Model):
    """Item de uma nota fiscal de entrada (produto/ingrediente)."""
    nota_fiscal = models.ForeignKey(
        NotaFiscalEntrada, on_delete=models.CASCADE, related_name='itens'
    )
    descricao = models.CharField(max_length=200, verbose_name='Descrição')
    quantidade = models.DecimalField(max_digits=12, decimal_places=3, default=1)
    unidade = models.CharField(max_length=10, default='UN')  # UN, KG, CX, etc.
    valor_unitario = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'restaurante_itens_nf_entrada'
        verbose_name = 'Item da NF'
        verbose_name_plural = 'Itens da NF'

    def __str__(self):
        return f"{self.descricao} x {self.quantidade}"


class EstoqueItem(LojaIsolationMixin, models.Model):
    """Item de estoque (ingrediente ou produto) do restaurante."""
    nome = models.CharField(max_length=200)
    unidade = models.CharField(max_length=10, default='UN')  # UN, KG, L, CX
    quantidade_atual = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    quantidade_minima = models.DecimalField(
        max_digits=12, decimal_places=3, default=0,
        help_text='Alerta quando estoque ficar abaixo'
    )
    observacoes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = 'restaurante_estoque_itens'
        ordering = ['nome']
        verbose_name = 'Item de Estoque'
        verbose_name_plural = 'Itens de Estoque'

    def __str__(self):
        return f"{self.nome} ({self.quantidade_atual} {self.unidade})"


class MovimentoEstoque(models.Model):
    """Movimentação de estoque (entrada/saída), opcionalmente vinculada a uma NF."""
    ENTRADA = 'entrada'
    SAIDA = 'saida'
    TIPO_CHOICES = [(ENTRADA, 'Entrada'), (SAIDA, 'Saída')]

    estoque_item = models.ForeignKey(
        EstoqueItem, on_delete=models.PROTECT, related_name='movimentos'
    )
    quantidade = models.DecimalField(max_digits=12, decimal_places=3)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    nota_fiscal = models.ForeignKey(
        NotaFiscalEntrada, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='movimentos_estoque'
    )
    observacao = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'restaurante_movimentos_estoque'
        ordering = ['-created_at']
        verbose_name = 'Movimento de Estoque'
        verbose_name_plural = 'Movimentos de Estoque'

    def __str__(self):
        return f"{self.tipo} {self.quantidade} - {self.estoque_item.nome}"


class RegistroPesoBalança(models.Model):
    """Registro de peso (balança) por item de estoque — integração com balança para pesar por kg."""
    estoque_item = models.ForeignKey(
        EstoqueItem, on_delete=models.PROTECT, related_name='registros_peso'
    )
    peso_kg = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='Peso (kg)')
    adicionar_ao_estoque = models.BooleanField(
        default=True,
        help_text='Se True, gera entrada no estoque com essa quantidade (kg)'
    )
    observacao = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'restaurante_registros_peso_balanca'
        ordering = ['-created_at']
        verbose_name = 'Registro de Peso (Balança)'
        verbose_name_plural = 'Registros de Peso (Balança)'

    def __str__(self):
        return f"{self.estoque_item.nome}: {self.peso_kg} kg"
