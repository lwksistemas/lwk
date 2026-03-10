"""
Models abstratos reutilizáveis para sistemas de agendamento
Usado por: clinica_estetica, clinica_beleza, cabeleireiro

Princípios SOLID:
- Single Responsibility: Cada model tem uma responsabilidade
- Open/Closed: Extensível via herança, fechado para modificação
- Liskov Substitution: Subclasses podem substituir classes base
- Interface Segregation: Interfaces específicas para cada tipo
- Dependency Inversion: Depende de abstrações (LojaIsolationMixin)
"""

from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from core.mixins import LojaIsolationMixin, LojaIsolationManager


class ClienteBase(LojaIsolationMixin, models.Model):
    """
    Model abstrato para Cliente/Paciente
    Reutilizável por todos os apps de agendamento
    """
    nome = models.CharField(max_length=200, verbose_name="Nome")
    email = models.EmailField(blank=True, null=True, verbose_name="E-mail")
    telefone = models.CharField(max_length=20, verbose_name="Telefone")
    cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name="CPF")
    data_nascimento = models.DateField(blank=True, null=True, verbose_name="Data de Nascimento")
    endereco = models.TextField(blank=True, null=True, verbose_name="Endereço")
    cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade")
    estado = models.CharField(max_length=2, blank=True, null=True, verbose_name="Estado")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    objects = LojaIsolationManager()

    class Meta:
        abstract = True  # ✅ Não cria tabela no banco
        ordering = ['-created_at']

    def __str__(self):
        return self.nome


class ProfissionalBase(LojaIsolationMixin, models.Model):
    """
    Model abstrato para Profissional
    Reutilizável por todos os apps de agendamento
    """
    nome = models.CharField(max_length=200, verbose_name="Nome")
    email = models.EmailField(blank=True, null=True, verbose_name="E-mail")
    telefone = models.CharField(max_length=20, verbose_name="Telefone")
    especialidade = models.CharField(max_length=100, verbose_name="Especialidade")
    registro_profissional = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        verbose_name="Registro Profissional",
        help_text="CRM, COREN, etc"
    )
    comissao_percentual = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Comissão %"
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    objects = LojaIsolationManager()

    class Meta:
        abstract = True
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} - {self.especialidade}"


class ServicoBase(LojaIsolationMixin, models.Model):
    """
    Model abstrato para Serviço/Procedimento
    Reutilizável por todos os apps de agendamento
    """
    nome = models.CharField(max_length=200, verbose_name="Nome")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    duracao_minutos = models.IntegerField(verbose_name="Duração (minutos)")
    preco = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Preço"
    )
    categoria = models.CharField(max_length=100, verbose_name="Categoria")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    objects = LojaIsolationManager()

    class Meta:
        abstract = True
        ordering = ['categoria', 'nome']

    def __str__(self):
        return f"{self.nome} - R$ {self.preco}"


class HorarioTrabalhoProfissionalBase(LojaIsolationMixin, models.Model):
    """
    Model abstrato para Horário de Trabalho do Profissional
    Reutilizável por todos os apps de agendamento
    """
    DIAS_SEMANA = [
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    # profissional será ForeignKey no model concreto
    dia_semana = models.IntegerField(choices=DIAS_SEMANA, verbose_name="Dia da semana")
    hora_entrada = models.TimeField(verbose_name="Entrada")
    hora_saida = models.TimeField(verbose_name="Saída")
    intervalo_inicio = models.TimeField(
        blank=True, 
        null=True,
        verbose_name="Início intervalo",
        help_text="Opcional (ex: almoço)"
    )
    intervalo_fim = models.TimeField(
        blank=True, 
        null=True,
        verbose_name="Fim intervalo"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    objects = LojaIsolationManager()

    class Meta:
        abstract = True
        ordering = ['dia_semana']

    def __str__(self):
        return f"{self.get_dia_semana_display()}: {self.hora_entrada}-{self.hora_saida}"


class BloqueioAgendaBase(LojaIsolationMixin, models.Model):
    """
    Model abstrato para Bloqueio de Agenda
    Reutilizável por todos os apps de agendamento
    """
    TIPO_BLOQUEIO = [
        ('feriado', 'Feriado'),
        ('ferias', 'Férias'),
        ('folga', 'Folga'),
        ('manutencao', 'Manutenção'),
        ('evento', 'Evento'),
        ('outros', 'Outros'),
    ]
    
    # profissional será ForeignKey no model concreto (null=True para bloqueio geral)
    titulo = models.CharField(max_length=200, verbose_name="Título")
    tipo = models.CharField(max_length=20, choices=TIPO_BLOQUEIO, verbose_name="Tipo")
    data_inicio = models.DateField(verbose_name="Data Início")
    data_fim = models.DateField(verbose_name="Data Fim")
    horario_inicio = models.TimeField(
        blank=True, 
        null=True, 
        verbose_name="Horário Início",
        help_text="Deixe vazio para bloquear o dia todo"
    )
    horario_fim = models.TimeField(blank=True, null=True, verbose_name="Horário Fim")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    
    objects = LojaIsolationManager()

    class Meta:
        abstract = True
        ordering = ['data_inicio']

    def __str__(self):
        return f"{self.titulo} - {self.data_inicio} a {self.data_fim}"
