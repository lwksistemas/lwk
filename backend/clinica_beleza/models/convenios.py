"""Models — convênios e locais de atendimento."""
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

from .procedures import Procedure

class LocalAtendimento(LojaIsolationMixin, models.Model):
    """Local de atendimento com valor de consulta associado (ex: Consultório, Home Care, Telemedicina)."""
    nome = models.CharField(max_length=200, verbose_name="Nome do local")
    valor_consulta = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor da consulta (R$)")
    tempo_consulta_minutos = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Tempo da consulta (minutos)",
        help_text="Duração padrão da consulta neste local (ex.: 40 minutos).",
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_locais_atendimento'
        ordering = ['nome']
        verbose_name = 'Local de atendimento'
        verbose_name_plural = 'Locais de atendimento'

    def __str__(self):
        return f"{self.nome} - R$ {self.valor_consulta}"


class NomeAgenda(LojaIsolationMixin, models.Model):
    """Nome/categoria de agenda exibida no calendário e nas consultas (ex: Estética, Dermatologia)."""
    nome = models.CharField(max_length=200, verbose_name="Nome da agenda")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_nomes_agenda'
        ordering = ['nome']
        verbose_name = 'Nome da agenda'
        verbose_name_plural = 'Nomes de agenda'

    def __str__(self):
        return self.nome


# ═══════════════════════════════════════════════════════════════════════════════
# CONVÊNIOS — Tabelas de preço por plano
# ═══════════════════════════════════════════════════════════════════════════════



class Convenio(LojaIsolationMixin, models.Model):
    """Plano de saúde / convênio com tabela de preços por procedimento."""
    nome = models.CharField(max_length=200, verbose_name='Nome')
    codigo = models.CharField(max_length=50, blank=True, default='', verbose_name='Código')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_convenios'
        ordering = ['nome']
        verbose_name = 'Convênio'
        verbose_name_plural = 'Convênios'

    def __str__(self):
        return self.nome




class ConvenioProcedimentoPreco(LojaIsolationMixin, models.Model):
    """Preço de um procedimento para um convênio específico (fixo ou % sobre particular)."""
    MODO_CHOICES = (
        ('fixo', 'Valor fixo (R$)'),
        ('percentual', 'Percentual (%)'),
    )

    convenio = models.ForeignKey(
        Convenio,
        on_delete=models.CASCADE,
        related_name='precos_procedimentos',
        verbose_name='Convênio',
    )
    procedure = models.ForeignKey(
        Procedure,
        on_delete=models.CASCADE,
        related_name='precos_convenio',
        verbose_name='Procedimento',
    )
    modo = models.CharField(
        max_length=15,
        choices=MODO_CHOICES,
        default='fixo',
        verbose_name='Modo',
    )
    preco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Valor',
        help_text='Valor fixo em R$ ou percentual sobre o preço particular (ex: 70 = 70%).',
    )
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_convenio_procedimento_precos'
        ordering = ['convenio', 'procedure__nome']
        verbose_name = 'Preço convênio × procedimento'
        verbose_name_plural = 'Preços convênio × procedimento'
        constraints = [
            models.UniqueConstraint(
                fields=['convenio', 'procedure', 'loja_id'],
                name='uniq_convenio_procedure_loja',
            ),
        ]

    def calcular_preco_efetivo(self, procedure=None):
        """Retorna o preço cobrado: fixo ou % do preço particular do procedimento."""
        procedure = procedure or self.procedure
        base = procedure.preco or Decimal('0')
        if self.modo == 'percentual':
            return (base * self.preco / Decimal('100')).quantize(Decimal('0.01'))
        return self.preco

    def __str__(self):
        if self.modo == 'percentual':
            return f'{self.convenio.nome} — {self.procedure.nome}: {self.preco}%'
        return f'{self.convenio.nome} — {self.procedure.nome}: R$ {self.preco}'
