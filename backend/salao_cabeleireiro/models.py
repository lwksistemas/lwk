"""Agenda do salão. Reusa os modelos abstratos da agenda e troca o vocabulário da clínica."""
from datetime import timedelta
from decimal import Decimal

from django.db import models

from core.mixins import LojaIsolationManager

from agenda_base.models import (
    BloqueioAgendaBase,
    ClienteBase,
    HorarioTrabalhoProfissionalBase,
    ProfissionalBase,
    ServicoBase,
)


PAINEIS = (
    ("operacao", "Operação do dia"),
    ("gestao", "Gestão do mês"),
    ("semana", "Agenda da semana"),
)

STATUS_AGENDAMENTO = (
    ("SCHEDULED", "Aguardando"),
    ("CONFIRMED", "Confirmado"),
    ("IN_PROGRESS", "Em atendimento"),
    ("COMPLETED", "Concluído"),
    ("CANCELLED", "Cancelado"),
    ("NO_SHOW", "Faltou"),
)

STATUS_OCUPA_HORARIO = ("SCHEDULED", "CONFIRMED", "IN_PROGRESS", "COMPLETED")

FORMAS_PAGAMENTO = (
    ("dinheiro", "Dinheiro"),
    ("pix", "Pix"),
    ("debito", "Débito"),
    ("credito", "Crédito"),
)


class SalaoConfig(models.Model):
    """Painel escolhido pelo administrador. Vale para a loja inteira."""

    loja_id = models.IntegerField(unique=True, db_index=True)
    painel = models.CharField(max_length=20, choices=PAINEIS, default="operacao")
    enviar_confirmacao = models.BooleanField(default=False)
    enviar_lembrete = models.BooleanField(default=False)
    lembrete_horas = models.PositiveSmallIntegerField(default=24)
    enviar_reagendamento = models.BooleanField(default=False)
    enviar_cancelamento = models.BooleanField(default=False)
    objects = LojaIsolationManager()

    def save(self, *args, **kwargs):
        from tenants.middleware import get_current_loja_id

        if not self.loja_id:
            atual = get_current_loja_id()
            if atual:
                self.loja_id = atual
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Configuração do salão"


class Cliente(ClienteBase):
    class Meta:
        verbose_name = "Cliente"
        ordering = ["nome"]


class Profissional(ProfissionalBase):
    class Meta:
        verbose_name = "Profissional"
        ordering = ["nome"]


class Servico(ServicoBase):
    class Meta:
        verbose_name = "Serviço"
        ordering = ["categoria", "nome"]


class HorarioTrabalho(HorarioTrabalhoProfissionalBase):
    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.CASCADE,
        related_name="horarios",
    )

    class Meta:
        verbose_name = "Horário de trabalho"
        ordering = ["dia_semana"]
        unique_together = [["profissional", "dia_semana"]]


class Bloqueio(BloqueioAgendaBase):
    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="bloqueios",
    )

    class Meta:
        verbose_name = "Bloqueio"
        ordering = ["data_inicio"]


class Agendamento(models.Model):
    loja_id = models.IntegerField(db_index=True)
    inicio = models.DateTimeField(verbose_name="Início")
    duracao_minutos = models.PositiveIntegerField(verbose_name="Duração (min)")
    status = models.CharField(max_length=20, choices=STATUS_AGENDAMENTO, default="SCHEDULED")
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="agendamentos")
    profissional = models.ForeignKey(Profissional, on_delete=models.PROTECT, related_name="agendamentos")
    servico = models.ForeignKey(Servico, on_delete=models.PROTECT, related_name="agendamentos")
    observacoes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = LojaIsolationManager()

    class Meta:
        verbose_name = "Agendamento"
        ordering = ["inicio"]
        indexes = [
            models.Index(fields=["loja_id", "inicio"]),
            models.Index(fields=["profissional", "inicio"]),
        ]

    @property
    def fim(self):
        return self.inicio + timedelta(minutes=int(self.duracao_minutos or 0))

    def save(self, *args, **kwargs):
        from tenants.middleware import get_current_loja_id

        if not self.loja_id:
            atual = get_current_loja_id()
            if atual:
                self.loja_id = atual
        super().save(*args, **kwargs)


class Recebimento(models.Model):
    """Dinheiro que entrou no caixa. O preço do serviço, sozinho, não é receita."""

    loja_id = models.IntegerField(db_index=True)
    agendamento = models.ForeignKey(Agendamento, on_delete=models.PROTECT, related_name="recebimentos")
    profissional = models.ForeignKey(Profissional, on_delete=models.PROTECT, related_name="recebimentos")
    valor_servico = models.DecimalField(max_digits=10, decimal_places=2)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    forma = models.CharField(max_length=20, choices=FORMAS_PAGAMENTO)
    partes = models.JSONField(default=list, blank=True)
    comissao_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"))
    comissao_valor = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    observacao = models.CharField(max_length=200, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = LojaIsolationManager()

    class Meta:
        verbose_name = "Recebimento"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["agendamento"],
                condition=models.Q(is_active=True),
                name="salao_um_recebimento_ativo",
            ),
        ]

    def save(self, *args, **kwargs):
        from tenants.middleware import get_current_loja_id

        if not self.loja_id:
            atual = get_current_loja_id()
            if atual:
                self.loja_id = atual
        super().save(*args, **kwargs)
