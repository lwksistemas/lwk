"""Models — estoque."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models

from agenda_base.models import (
    BloqueioAgendaBase,
    ClienteBase,
    HorarioTrabalhoProfissionalBase,
    ProfissionalBase,
    ServicoBase,
)
from core.mixins import LojaIsolationManager, LojaIsolationMixin

User = get_user_model()

from .appointments import Appointment
from .professionals import Professional
from .procedures import Procedure

class ProdutoEstoque(LojaIsolationMixin, models.Model):
    """Produto do estoque da clínica (botox, ácido hialurônico, soro, etc.)"""
    CATEGORIA_CHOICES = [
        ('injetavel', 'Injetável'),
        ('soroterapia', 'Soroterapia'),
        ('cosmético', 'Cosmético'),
        ('medicamentos', 'Medicamentos'),
        ('descartavel', 'Descartável'),
        ('equipamento', 'Equipamento'),
        ('outro', 'Outro'),
    ]

    nome = models.CharField(max_length=200, verbose_name="Nome do produto")
    categoria = models.CharField(max_length=30, choices=CATEGORIA_CHOICES, default='outro', verbose_name="Categoria")
    marca = models.CharField(max_length=100, blank=True, default='', verbose_name="Marca/Fabricante")
    unidade_medida = models.CharField(max_length=30, default='unidade', verbose_name="Unidade de medida",
                                      help_text="Ex: unidade, ml, mg, ampola, frasco")
    quantidade_atual = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Quantidade atual")
    quantidade_minima = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Estoque mínimo",
                                            help_text="Alerta quando atingir este valor")
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Preço de custo (R$)")
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Preço de venda (R$)")
    validade = models.DateField(null=True, blank=True, verbose_name="Data de validade")
    lote = models.CharField(max_length=50, blank=True, default='', verbose_name="Lote")
    numero_nota = models.CharField(
        max_length=50, blank=True, default='', verbose_name="Número da nota fiscal",
    )
    observacoes = models.TextField(blank=True, default='', verbose_name="Observações")
    procedure = models.ForeignKey(
        Procedure,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='produtos_estoque',
        verbose_name='Procedimento vinculado',
        help_text='Vincula o produto ao procedimento (ex.: termo de consentimento).',
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    dias_alerta_validade = models.PositiveIntegerField(
        default=90,
        verbose_name="Dias para alerta de validade",
        help_text="Quantidade de dias antes do vencimento para emitir alerta (ex: 90).",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        verbose_name = "Produto do estoque"
        verbose_name_plural = "Produtos do estoque"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.quantidade_atual} {self.unidade_medida})"

    @property
    def estoque_baixo(self):
        """Retorna True se estoque está abaixo do mínimo."""
        return self.quantidade_atual <= self.quantidade_minima

    @property
    def validade_proxima(self):
        """Retorna True se a validade está dentro do período de alerta."""
        if not self.validade:
            return False
        from datetime import date, timedelta
        limite = date.today() + timedelta(days=self.dias_alerta_validade)
        return self.validade <= limite




class MovimentacaoEstoque(LojaIsolationMixin, models.Model):
    """Registro de entrada/saída de produtos do estoque."""
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
        ('ajuste', 'Ajuste de inventário'),
    ]

    produto = models.ForeignKey(ProdutoEstoque, on_delete=models.CASCADE, related_name='movimentacoes')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantidade")
    motivo = models.CharField(max_length=200, blank=True, default='', verbose_name="Motivo/Observação")
    profissional = models.ForeignKey(Professional, on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name="Profissional responsável")
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name="Agendamento vinculado")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data da movimentação")

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        verbose_name = "Movimentação de estoque"
        verbose_name_plural = "Movimentações de estoque"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.produto.nome} ({self.quantidade})"


class ConsultaProdutoUtilizado(LojaIsolationMixin, models.Model):
    """Produto do estoque utilizado em uma consulta (baixa ao finalizar)."""
    consulta = models.ForeignKey(
        'Consulta',
        on_delete=models.CASCADE,
        related_name='produtos_estoque',
        verbose_name='Consulta',
    )
    produto = models.ForeignKey(
        ProdutoEstoque,
        on_delete=models.PROTECT,
        related_name='uso_em_consultas',
        verbose_name='Produto',
    )
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Quantidade utilizada')
    lote = models.CharField(max_length=50, blank=True, default='', verbose_name='Lote utilizado')
    validade = models.DateField(null=True, blank=True, verbose_name='Validade do lote')
    estoque_baixado = models.BooleanField(default=False, verbose_name='Estoque já baixado')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Registrado em')

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        verbose_name = 'Produto utilizado na consulta'
        verbose_name_plural = 'Produtos utilizados na consulta'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.produto.nome} x{self.quantidade} (consulta {self.consulta_id})'


