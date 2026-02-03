from django.db import models
from core.models import BaseCategoria, BaseCliente, BaseFuncionario
from core.mixins import LojaIsolationMixin


class Categoria(LojaIsolationMixin, BaseCategoria):
    """Categorias de serviços"""
    
    class Meta:
        db_table = 'servicos_categorias'
        ordering = ['nome']
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'


class Servico(LojaIsolationMixin, models.Model):
    """Serviços oferecidos"""
    nome = models.CharField(max_length=200)
    descricao = models.TextField()
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, related_name='servicos')
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    duracao_estimada = models.IntegerField(help_text='Duração em minutos')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'servicos_servicos'
        ordering = ['categoria', 'nome']
        verbose_name = 'Serviço'
        verbose_name_plural = 'Serviços'

    def __str__(self):
        return f"{self.nome} - R$ {self.preco}"


class Cliente(LojaIsolationMixin, BaseCliente):
    """Clientes"""
    tipo_cliente = models.CharField(max_length=20, choices=[('pf', 'Pessoa Física'), ('pj', 'Pessoa Jurídica')], default='pf')
    observacoes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'servicos_clientes'
        ordering = ['-created_at']
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'


class Profissional(LojaIsolationMixin, models.Model):
    """Profissionais que executam os serviços"""
    nome = models.CharField(max_length=200)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    especialidade = models.CharField(max_length=100)
    registro_profissional = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'servicos_profissionais'
        ordering = ['nome']
        verbose_name = 'Profissional'
        verbose_name_plural = 'Profissionais'

    def __str__(self):
        return f"{self.nome} - {self.especialidade}"


class Agendamento(LojaIsolationMixin, models.Model):
    """Agendamentos de serviços"""
    STATUS_CHOICES = [
        ('agendado', 'Agendado'),
        ('confirmado', 'Confirmado'),
        ('em_andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='agendamentos')
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE, related_name='agendamentos')
    profissional = models.ForeignKey(Profissional, on_delete=models.SET_NULL, null=True, related_name='agendamentos')
    data = models.DateField()
    horario = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='agendado')
    endereco_atendimento = models.TextField(blank=True, null=True, help_text='Se o serviço for no local do cliente')
    observacoes = models.TextField(blank=True, null=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'servicos_agendamentos'
        ordering = ['data', 'horario']
        verbose_name = 'Agendamento'
        verbose_name_plural = 'Agendamentos'

    def __str__(self):
        return f"{self.cliente.nome} - {self.servico.nome} - {self.data} {self.horario}"


class OrdemServico(LojaIsolationMixin, models.Model):
    """Ordens de serviço"""
    STATUS_CHOICES = [
        ('aberta', 'Aberta'),
        ('em_andamento', 'Em Andamento'),
        ('aguardando_peca', 'Aguardando Peça'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
    ]

    numero_os = models.CharField(max_length=20, unique=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='ordens_servico')
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE, related_name='ordens_servico')
    profissional = models.ForeignKey(Profissional, on_delete=models.SET_NULL, null=True, related_name='ordens_servico')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aberta')
    descricao_problema = models.TextField()
    diagnostico = models.TextField(blank=True, null=True)
    solucao = models.TextField(blank=True, null=True)
    
    data_abertura = models.DateField(auto_now_add=True)
    data_previsao = models.DateField(blank=True, null=True)
    data_conclusao = models.DateField(blank=True, null=True)
    
    valor_servico = models.DecimalField(max_digits=10, decimal_places=2)
    valor_pecas = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    observacoes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'servicos_ordens_servico'
        ordering = ['-created_at']
        verbose_name = 'Ordem de Serviço'
        verbose_name_plural = 'Ordens de Serviço'

    def __str__(self):
        return f"OS #{self.numero_os} - {self.cliente.nome}"


class Orcamento(LojaIsolationMixin, models.Model):
    """Orçamentos"""
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('recusado', 'Recusado'),
        ('expirado', 'Expirado'),
    ]

    numero_orcamento = models.CharField(max_length=20, unique=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='orcamentos')
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE, related_name='orcamentos')
    
    descricao = models.TextField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    validade = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    
    observacoes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'servicos_orcamentos'
        ordering = ['-created_at']
        verbose_name = 'Orçamento'
        verbose_name_plural = 'Orçamentos'

    def __str__(self):
        return f"Orçamento #{self.numero_orcamento} - {self.cliente.nome}"


class Funcionario(LojaIsolationMixin, BaseFuncionario):
    """Funcionários"""

    class Meta:
        db_table = 'servicos_funcionarios'
        ordering = ['nome']
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'
