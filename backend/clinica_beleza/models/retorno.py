"""Configuração de retorno gratuito (isenção da taxa de consulta)."""
from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin

from .procedures import Procedure


class AgendaRetornoConfig(LojaIsolationMixin, models.Model):
    """
    Configuração geral de retorno por loja.
    O administrador ativa cada modo e define o prazo (consulta) ou regras por procedimento.
    """
    retorno_procedimento_ativo = models.BooleanField(
        default=False,
        verbose_name='Retorno por procedimento ativo',
        help_text='Isenta taxa de consulta quando o paciente retorna para acompanhamento do procedimento.',
    )
    retorno_consulta_ativo = models.BooleanField(
        default=False,
        verbose_name='Retorno por consulta ativo',
        help_text='Isenta taxa de consulta quando o paciente teve consulta concluída dentro do prazo.',
    )
    dias_retorno_consulta = models.PositiveIntegerField(
        default=30,
        verbose_name='Prazo retorno por consulta (dias)',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_agenda_retorno_config'
        verbose_name = 'Configuração de retorno da agenda'
        verbose_name_plural = 'Configurações de retorno da agenda'

    def __str__(self):
        partes = []
        if self.retorno_procedimento_ativo:
            partes.append('procedimento')
        if self.retorno_consulta_ativo:
            partes.append(f'consulta {self.dias_retorno_consulta}d')
        return ', '.join(partes) or 'inativo'


class RetornoProcedimentoRegra(LojaIsolationMixin, models.Model):
    """Prazo de retorno gratuito por procedimento (acompanhamento pós-procedimento)."""
    procedure = models.ForeignKey(
        Procedure,
        on_delete=models.CASCADE,
        related_name='regras_retorno',
        verbose_name='Procedimento',
    )
    dias_retorno = models.PositiveIntegerField(
        verbose_name='Prazo (dias)',
        help_text='Dias após o procedimento concluído em que a taxa de consulta não é cobrada.',
    )
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_retorno_procedimento_regra'
        ordering = ['procedure__nome']
        verbose_name = 'Regra de retorno por procedimento'
        verbose_name_plural = 'Regras de retorno por procedimento'
        constraints = [
            models.UniqueConstraint(
                fields=['procedure', 'loja_id'],
                name='uniq_retorno_procedimento_loja',
            ),
        ]

    def __str__(self):
        return f'{self.procedure.nome} — {self.dias_retorno} dias'
