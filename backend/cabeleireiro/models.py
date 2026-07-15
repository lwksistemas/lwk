"""Models do app Salão (cabeleireiro) — multi-tenant por schema."""
from datetime import datetime, time
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from agenda_base.models import BloqueioAgendaBase, ClienteBase, ProfissionalBase, ServicoBase
from core.mixins import LojaIsolationManager, LojaIsolationMixin


class Cliente(ClienteBase):
    """Cliente do salão (mesmo padrão de paciente da clínica, sem prontuário)."""

    allow_whatsapp = models.BooleanField(default=True, verbose_name="Permitir WhatsApp")
    foto_url = models.URLField(blank=True, default="", max_length=500, verbose_name="Foto")
    cep = models.CharField(max_length=10, blank=True, default="", verbose_name="CEP")
    logradouro = models.CharField(max_length=200, blank=True, default="")
    numero = models.CharField(max_length=20, blank=True, default="")
    complemento = models.CharField(max_length=100, blank=True, default="")
    bairro = models.CharField(max_length=100, blank=True, default="")

    class Meta(ClienteBase.Meta):
        app_label = "cabeleireiro"
        db_table = "cabeleireiro_cliente"
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nome"]


class Profissional(ProfissionalBase):
    """Profissional do salão (sem Memed/prescritor)."""

    especialidade = models.CharField(
        max_length=100,
        blank=True,
        default="Cabeleireiro(a)",
        verbose_name="Especialidade",
    )
    cor_agenda = models.CharField(max_length=7, blank=True, default="#4A3042")

    class Meta(ProfissionalBase.Meta):
        app_label = "cabeleireiro"
        db_table = "cabeleireiro_profissional"
        verbose_name = "Profissional"
        verbose_name_plural = "Profissionais"


class Servico(ServicoBase):
    """Serviço oferecido no salão."""

    categoria = models.CharField(max_length=100, blank=True, default="Geral", verbose_name="Categoria")

    class Meta(ServicoBase.Meta):
        app_label = "cabeleireiro"
        db_table = "cabeleireiro_servico"
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"


class Agendamento(LojaIsolationMixin, models.Model):
    """Agendamento / atendimento do salão."""

    STATUS_SCHEDULED = "SCHEDULED"
    STATUS_CLIENT_CONFIRMED = "CLIENT_CONFIRMED"
    STATUS_ARRIVED = "ARRIVED"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_DONE = "DONE"
    STATUS_NO_SHOW = "NO_SHOW"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_CHOICES = [
        (STATUS_SCHEDULED, "Agendado"),
        (STATUS_CLIENT_CONFIRMED, "Confirmado pelo cliente"),
        (STATUS_ARRIVED, "Chegou"),
        (STATUS_IN_PROGRESS, "Em atendimento"),
        (STATUS_DONE, "Concluído"),
        (STATUS_NO_SHOW, "Não compareceu"),
        (STATUS_CANCELLED, "Cancelado"),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="agendamentos",
    )
    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.PROTECT,
        related_name="agendamentos",
        null=True,
        blank=True,
    )
    servico = models.ForeignKey(
        Servico,
        on_delete=models.PROTECT,
        related_name="agendamentos",
        null=True,
        blank=True,
    )
    data = models.DateField(verbose_name="Data")
    hora_inicio = models.TimeField(verbose_name="Início")
    hora_fim = models.TimeField(null=True, blank=True, verbose_name="Fim")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_SCHEDULED,
    )
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    observacoes = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "cabeleireiro"
        db_table = "cabeleireiro_agendamento"
        ordering = ["data", "hora_inicio"]
        indexes = [
            models.Index(fields=["loja_id", "data", "status"]),
            models.Index(fields=["loja_id", "profissional", "data"]),
        ]

    def __str__(self):
        return f"{self.cliente_id} @ {self.data} {self.hora_inicio}"


class BloqueioHorario(BloqueioAgendaBase):
    """Bloqueio de horário na agenda do salão (mesmo padrão da clínica)."""

    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="bloqueios",
        verbose_name="Profissional",
        help_text="Vazio = bloqueio geral (todos)",
    )
    motivo = models.CharField(max_length=100, verbose_name="Motivo")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    @property
    def data_inicio_dt(self):
        if self.horario_inicio:
            return datetime.combine(self.data_inicio, self.horario_inicio)
        return datetime.combine(self.data_inicio, time.min)

    @property
    def data_fim_dt(self):
        if self.horario_fim:
            return datetime.combine(self.data_fim, self.horario_fim)
        return datetime.combine(self.data_fim, time.max)

    class Meta(BloqueioAgendaBase.Meta):
        app_label = "cabeleireiro"
        db_table = "cabeleireiro_bloqueiohorario"
        verbose_name = "Bloqueio de Horário"
        verbose_name_plural = "Bloqueios de Horário"
        ordering = ["-data_inicio"]
        indexes = [
            models.Index(fields=["data_inicio", "data_fim"], name="cab_bloq_data_idx"),
            models.Index(fields=["profissional", "data_inicio"], name="cab_bloq_prof_idx"),
            models.Index(fields=["loja_id", "data_inicio"], name="cab_bloq_loja_idx"),
        ]

    def __str__(self):
        return f"{self.motivo} ({self.data_inicio} - {self.data_fim})"

    def save(self, *args, **kwargs):
        if not self.titulo:
            self.titulo = self.motivo
        if not self.tipo:
            self.tipo = "outros"
        super().save(*args, **kwargs)
