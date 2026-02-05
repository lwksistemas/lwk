from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from core.mixins import LojaIsolationMixin, LojaIsolationManager


class Cliente(LojaIsolationMixin, models.Model):
    """Cliente do cabeleireiro"""
    nome = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20)
    cpf = models.CharField(max_length=14, blank=True, null=True)
    data_nascimento = models.DateField(blank=True, null=True)
    endereco = models.TextField(blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = LojaIsolationManager()

    class Meta:
        app_label = 'cabeleireiro'
        db_table = 'cabeleireiro_clientes'
        ordering = ['-created_at']
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return self.nome


class Profissional(LojaIsolationMixin, models.Model):
    """Profissionais do cabeleireiro (MODELO ANTIGO - Manter para compatibilidade)"""
    nome = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20)
    especialidade = models.CharField(max_length=100, blank=True, null=True)
    comissao_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = LojaIsolationManager()

    class Meta:
        app_label = 'cabeleireiro'
        db_table = 'cabeleireiro_profissionais'
        ordering = ['nome']
        verbose_name = 'Profissional (Antigo)'
        verbose_name_plural = 'Profissionais (Antigo)'

    def __str__(self):
        return self.nome


class Servico(LojaIsolationMixin, models.Model):
    """Serviços oferecidos pelo cabeleireiro"""
    CATEGORIA_CHOICES = [
        ('corte', 'Corte'),
        ('coloracao', 'Coloração'),
        ('tratamento', 'Tratamento'),
        ('penteado', 'Penteado'),
        ('manicure', 'Manicure/Pedicure'),
        ('barba', 'Barba'),
        ('depilacao', 'Depilação'),
        ('maquiagem', 'Maquiagem'),
        ('outros', 'Outros'),
    ]
    
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    duracao_minutos = models.IntegerField(help_text='Duração em minutos')
    preco = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = LojaIsolationManager()

    class Meta:
        app_label = 'cabeleireiro'
        db_table = 'cabeleireiro_servicos'
        ordering = ['categoria', 'nome']
        verbose_name = 'Serviço'
        verbose_name_plural = 'Serviços'

    def __str__(self):
        return f"{self.nome} - R$ {self.preco}"


class Agendamento(LojaIsolationMixin, models.Model):
    """Agendamentos de serviços"""
    STATUS_CHOICES = [
        ('agendado', 'Agendado'),
        ('confirmado', 'Confirmado'),
        ('em_atendimento', 'Em Atendimento'),
        ('concluído', 'Concluído'),
        ('cancelado', 'Cancelado'),
        ('falta', 'Falta'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='agendamentos')
    profissional = models.ForeignKey('Profissional', on_delete=models.SET_NULL, null=True, related_name='agendamentos')
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE, related_name='agendamentos')
    data = models.DateField()
    horario = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='agendado')
    observacoes = models.TextField(blank=True, null=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    forma_pagamento = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = LojaIsolationManager()

    class Meta:
        app_label = 'cabeleireiro'
        db_table = 'cabeleireiro_agendamentos'
        ordering = ['-data', '-horario']
        verbose_name = 'Agendamento'
        verbose_name_plural = 'Agendamentos'

    def __str__(self):
        return f"{self.cliente.nome} - {self.servico.nome} - {self.data} {self.horario}"


class Produto(LojaIsolationMixin, models.Model):
    """Produtos vendidos no cabeleireiro"""
    CATEGORIA_CHOICES = [
        ('shampoo', 'Shampoo'),
        ('condicionador', 'Condicionador'),
        ('mascara', 'Máscara'),
        ('finalizador', 'Finalizador'),
        ('coloracao', 'Coloração'),
        ('tratamento', 'Tratamento'),
        ('acessorio', 'Acessório'),
        ('outros', 'Outros'),
    ]
    
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    marca = models.CharField(max_length=100, blank=True, null=True)
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    estoque_atual = models.IntegerField(default=0)
    estoque_minimo = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = LojaIsolationManager()

    class Meta:
        app_label = 'cabeleireiro'
        db_table = 'cabeleireiro_produtos'
        ordering = ['categoria', 'nome']
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'

    def __str__(self):
        return f"{self.nome} - R$ {self.preco_venda}"


class Venda(LojaIsolationMixin, models.Model):
    """Vendas de produtos"""
    FORMA_PAGAMENTO_CHOICES = [
        ('dinheiro', 'Dinheiro'),
        ('debito', 'Débito'),
        ('credito', 'Crédito'),
        ('pix', 'PIX'),
        ('outros', 'Outros'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='vendas')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='vendas')
    quantidade = models.IntegerField(validators=[MinValueValidator(1)])
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    forma_pagamento = models.CharField(max_length=20, choices=FORMA_PAGAMENTO_CHOICES)
    data_venda = models.DateTimeField(auto_now_add=True)
    observacoes = models.TextField(blank=True, null=True)
    
    objects = LojaIsolationManager()

    class Meta:
        app_label = 'cabeleireiro'
        db_table = 'cabeleireiro_vendas'
        ordering = ['-data_venda']
        verbose_name = 'Venda'
        verbose_name_plural = 'Vendas'

    def __str__(self):
        return f"Venda #{self.id} - {self.produto.nome} - R$ {self.valor_total}"

    def save(self, *args, **kwargs):
        # Calcular valor total
        self.valor_total = self.quantidade * self.valor_unitario
        super().save(*args, **kwargs)


class Funcionario(LojaIsolationMixin, models.Model):
    """Funcionários do cabeleireiro (recepcionistas, auxiliares, profissionais, etc)"""
    
    # Níveis de permissão/função
    FUNCAO_CHOICES = [
        ('administrador', 'Administrador'),           # Acesso total
        ('gerente', 'Gerente'),                       # Acesso quase total (sem financeiro)
        ('atendente', 'Atendente/Recepcionista'),    # Agendamentos, clientes
        ('profissional', 'Profissional/Cabeleireiro'), # Atende clientes + sua agenda
        ('caixa', 'Caixa'),                          # Vendas e pagamentos
        ('estoquista', 'Estoquista'),                # Produtos e estoque
        ('visualizador', 'Visualizador'),            # Apenas leitura
    ]
    
    nome = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20)
    cpf = models.CharField(max_length=14, blank=True, null=True)
    
    # Separar cargo (descritivo) de função (permissões)
    cargo = models.CharField(max_length=100, help_text='Cargo descritivo (ex: Recepcionista, Cabeleireiro)')
    funcao = models.CharField(
        max_length=20, 
        choices=FUNCAO_CHOICES, 
        default='atendente',
        help_text='Define as permissões de acesso ao sistema'
    )
    
    # Campos específicos para profissionais que atendem
    especialidade = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text='Ex: Coloração, Corte Masculino, Penteados (para profissionais)'
    )
    comissao_percentual = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Comissão sobre serviços realizados (para profissionais)'
    )
    
    salario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    data_admissao = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = LojaIsolationManager()

    class Meta:
        app_label = 'cabeleireiro'
        db_table = 'cabeleireiro_funcionarios'
        ordering = ['nome']
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'

    def __str__(self):
        return f"{self.nome} - {self.get_funcao_display()}"
    
    @property
    def is_profissional(self):
        """Verifica se o funcionário é um profissional que atende clientes"""
        return self.funcao == 'profissional'


class HorarioFuncionamento(LojaIsolationMixin, models.Model):
    """Horários de funcionamento do cabeleireiro"""
    DIA_SEMANA_CHOICES = [
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    dia_semana = models.IntegerField(choices=DIA_SEMANA_CHOICES)
    horario_abertura = models.TimeField()
    horario_fechamento = models.TimeField()
    is_active = models.BooleanField(default=True)
    
    objects = LojaIsolationManager()

    class Meta:
        app_label = 'cabeleireiro'
        db_table = 'cabeleireiro_horarios'
        ordering = ['dia_semana']
        verbose_name = 'Horário de Funcionamento'
        verbose_name_plural = 'Horários de Funcionamento'

    def __str__(self):
        return f"{self.get_dia_semana_display()}: {self.horario_abertura} - {self.horario_fechamento}"


class BloqueioAgenda(LojaIsolationMixin, models.Model):
    """Bloqueios de agenda (férias, folgas, etc)"""
    profissional = models.ForeignKey('Profissional', on_delete=models.CASCADE, related_name='bloqueios',
                                     null=True, blank=True,
                                     help_text='Deixe em branco para bloquear agenda de todos os profissionais')
    data_inicio = models.DateField()
    data_fim = models.DateField()
    motivo = models.CharField(max_length=200)
    observacoes = models.TextField(blank=True, null=True)
    
    objects = LojaIsolationManager()

    class Meta:
        app_label = 'cabeleireiro'
        db_table = 'cabeleireiro_bloqueios'
        ordering = ['-data_inicio']
        verbose_name = 'Bloqueio de Agenda'
        verbose_name_plural = 'Bloqueios de Agenda'

    def __str__(self):
        prof_nome = self.profissional.nome if self.profissional else 'Todos'
        return f"{prof_nome} - {self.data_inicio} a {self.data_fim}"
