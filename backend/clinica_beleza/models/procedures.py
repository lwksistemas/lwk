"""Models — procedimentos e protocolos."""
from decimal import Decimal

from django.db import models

from agenda_base.models import ServicoBase
from core.mixins import LojaIsolationManager, LojaIsolationMixin


class Procedure(ServicoBase):
    """Procedimentos/Serviços oferecidos (herda de ServicoBase)"""
    termo_consentimento = models.TextField(
        blank=True, default='', verbose_name='Termo de consentimento esclarecido',
        help_text='Use {paciente_nome}, {profissional_nome}, {clinica_nome}, {procedimentos}, {data}.',
    )
    termo_consentimento_ativo = models.BooleanField(
        default=False, verbose_name='Exigir termo de consentimento',
    )

    class Meta(ServicoBase.Meta):
        app_label = 'clinica_beleza'
        verbose_name = "Procedimento"
        verbose_name_plural = "Procedimentos"
        ordering = ['nome']

    def __str__(self):
        return self.nome




class ProcedureProtocol(LojaIsolationMixin, models.Model):
    """Protocolos padronizados vinculados a procedimentos (Clínica da Beleza)."""
    nome = models.CharField(max_length=200, verbose_name='Nome do protocolo')
    procedure = models.ForeignKey(
        Procedure,
        on_delete=models.CASCADE,
        related_name='protocolos',
        verbose_name='Procedimento',
    )
    descricao = models.TextField(blank=True, default='', verbose_name='Descrição')
    preparacao = models.TextField(blank=True, default='', verbose_name='Preparação')
    execucao = models.TextField(blank=True, default='', verbose_name='Execução')
    pos_procedimento = models.TextField(blank=True, default='', verbose_name='Pós-procedimento')
    tempo_estimado = models.PositiveIntegerField(default=30, verbose_name='Tempo estimado (min)')
    materiais_necessarios = models.TextField(blank=True, default='', verbose_name='Materiais necessários')
    contraindicacoes = models.TextField(blank=True, default='', verbose_name='Contraindicações')
    cuidados_especiais = models.TextField(blank=True, default='', verbose_name='Cuidados especiais')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_protocolos'
        ordering = ['procedure__nome', 'nome']
        verbose_name = 'Protocolo de procedimento'
        verbose_name_plural = 'Protocolos de procedimentos'

    def __str__(self):
        return f'{self.procedure.nome} — {self.nome}'


