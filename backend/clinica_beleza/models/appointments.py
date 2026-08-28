"""Models — agendamentos e bloqueios."""
from decimal import Decimal

from django.db import models

from agenda_base.models import (
    BloqueioAgendaBase,
)
from core.mixins import LojaIsolationManager, LojaIsolationMixin

from .convenios import LocalAtendimento, NomeAgenda
from .patients import Patient
from .procedures import Procedure
from .professionals import Professional


def _taxa_base_agenda(local_atendimento=None, consulta=None) -> Decimal:
    """Taxa de consulta a partir do local ou da consulta vinculada."""
    if local_atendimento is not None:
        return Decimal(str(getattr(local_atendimento, "valor_consulta", 0) or 0))
    if consulta is not None:
        vc = Decimal(str(getattr(consulta, "valor_consulta", 0) or 0))
        if vc > 0:
            return vc
    return Decimal(0)


def _aplicar_retorno_na_taxa(
    taxa: Decimal,
    *,
    appointment=None,
    consulta=None,
    retorno_elegivel=None,
) -> Decimal:
    """Zera taxa quando o atendimento é retorno gratuito elegível."""
    if taxa <= 0:
        return taxa
    if retorno_elegivel is True:
        return Decimal(0)
    if retorno_elegivel is False:
        return taxa
    if appointment is not None:
        from ..retorno_service import verificar_retorno_appointment
        if verificar_retorno_appointment(appointment).elegivel:
            return Decimal(0)
    elif consulta is not None and getattr(consulta, "retorno_gratuito", False):
        return Decimal(0)
    return taxa


def _fallback_valor_agenda(
    total_proc: Decimal,
    taxa: Decimal,
    *,
    consulta=None,
    procedure=None,
    procedure_id=None,
) -> Decimal:
    """Quando não há local: procedimentos, taxa, valor da consulta ou preço legado."""
    if total_proc > 0:
        return total_proc
    if taxa > 0:
        return taxa
    if consulta is not None and not getattr(consulta, "retorno_gratuito", False):
        vc = Decimal(str(getattr(consulta, "valor_consulta", 0) or 0))
        if vc > 0:
            return vc
    if procedure_id and procedure is not None:
        return Decimal(str(getattr(procedure, "preco", 0) or 0))
    return Decimal(0)


def calcular_valor_exibicao_agenda(
    proc_total,
    *,
    local_atendimento=None,
    consulta=None,
    procedure=None,
    procedure_id=None,
    appointment=None,
    retorno_elegivel=None,
) -> Decimal:
    """Valor exibido na agenda: taxa do local + procedimentos (sem duplicar legacy procedure)."""
    total_proc = Decimal(str(proc_total or 0))
    taxa = _taxa_base_agenda(local_atendimento, consulta)
    taxa = _aplicar_retorno_na_taxa(
        taxa,
        appointment=appointment,
        consulta=consulta,
        retorno_elegivel=retorno_elegivel,
    )
    if local_atendimento is not None:
        return taxa + total_proc
    return _fallback_valor_agenda(
        total_proc,
        taxa,
        consulta=consulta,
        procedure=procedure,
        procedure_id=procedure_id,
    )


class Appointment(LojaIsolationMixin, models.Model):
    """Agendamentos"""

    STATUS_CHOICES = (
        ("CONFIRMED", "Cliente presente"),
        ("CLIENT_CONFIRMED", "Confirmado pelo WhatsApp"),
        ("PHONE_CONFIRMED", "Confirmado por ligação"),
        ("PENDING", "Aguardando confirmação"),  # legado — rodar normalizar_status_agenda antes de remover
        ("SCHEDULED", "Aguardando confirmação"),
        ("IN_PROGRESS", "Em Atendimento"),
        ("COMPLETED", "Consulta finalizada"),
        ("CANCELLED", "Cancelado"),
        ("NO_SHOW", "Faltou"),
    )

    date = models.DateTimeField(verbose_name="Data e Hora")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="SCHEDULED", verbose_name="Status")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name="Paciente")
    professional = models.ForeignKey(
        Professional, on_delete=models.SET_NULL, verbose_name="Profissional",
        null=True, blank=True,
        help_text="Profissional responsável. Pode ser definido ao iniciar a consulta.",
    )
    procedure = models.ForeignKey(
        Procedure, on_delete=models.CASCADE, verbose_name="Procedimento principal",
        null=True, blank=True,
        help_text="Legado: procedimento único. Use appointment_procedures para múltiplos.",
    )
    procedures = models.ManyToManyField(
        Procedure, through="AppointmentProcedure",
        related_name="appointments_multi", blank=True,
        verbose_name="Procedimentos",
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Observações")
    convenio = models.ForeignKey(
        "Convenio",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agendamentos",
        verbose_name="Convênio",
        help_text="Convênio do atendimento (define preços dos procedimentos).",
    )
    nome_agenda = models.ForeignKey(
        NomeAgenda,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agendamentos",
        verbose_name="Nome da agenda",
    )
    local_atendimento = models.ForeignKey(
        LocalAtendimento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agendamentos",
        verbose_name="Local de atendimento",
    )
    retorno_procedure = models.ForeignKey(
        Procedure,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agendamentos_retorno",
        verbose_name="Retorno do procedimento",
        help_text="Indica retorno de acompanhamento deste procedimento (sem repetir cobrança da consulta).",
    )
    duracao_minutos = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Duração efetiva (min)",
        help_text="Opcional. Se vazio, usa a duração cadastrada do procedimento.",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    # Sincronização offline: version para detectar conflitos; updated_by_id = ID do user (schema public)
    version = models.PositiveIntegerField(default=1, verbose_name="Versão")
    updated_by_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="Atualizado por (user id)")
    confirmacao_generation = models.PositiveIntegerField(
        default=1,
        verbose_name="Geração da confirmação",
        help_text="Incrementado ao alterar data, profissional ou procedimento. Invalida o link WhatsApp anterior.",
    )

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["date", "status"]),
            models.Index(fields=["professional", "date"]),
            models.Index(fields=["patient", "date"]),
            models.Index(fields=["loja_id", "date"]),
        ]

    def __str__(self):
        # Evita N+1: só usa procedures se já estiver no prefetch cache.
        cached = getattr(self, "_prefetched_objects_cache", {}) or {}
        if "procedures" in cached:
            nomes = ", ".join(p.nome for p in cached["procedures"]) or "—"
        elif self.procedure_id:
            nomes = f"proc#{self.procedure_id}"
        else:
            nomes = "—"
        paciente = f"paciente#{self.patient_id}"
        return f"{paciente} - {nomes} - {self.date.strftime('%d/%m/%Y %H:%M')}"

    def _linhas_procedimentos(self):
        """Usa o prefetch da listagem; .select_related() no related manager dispara N+1."""
        return list(self.appointment_procedures.all())

    def get_duracao_efetiva(self) -> int:
        """Duração efetiva: manual > max(procedimentos, tempo consulta do profissional)."""
        cached = getattr(self, "_duracao_efetiva_cache", None)
        if cached is not None:
            return cached
        from ..duracao_consulta import calcular_duracao_efetiva_agendamento

        result = calcular_duracao_efetiva_agendamento(
            duracao_manual=self.duracao_minutos,
            professional=self.professional,
            local_atendimento=self.local_atendimento,
            appointment_procedures=self._linhas_procedimentos() or None,
            procedure_principal=self.procedure if self.procedure_id else None,
        )
        self._duracao_efetiva_cache = result
        return result

    @property
    def valor_total(self):
        """Valor total: soma dos preços de todos os procedimentos."""
        cached = getattr(self, "_valor_total_cache", None)
        if cached is not None:
            return cached
        from decimal import Decimal
        total = sum(
            (ap.valor or ap.procedure.preco or Decimal(0))
            for ap in self._linhas_procedimentos()
        )
        if total > 0:
            self._valor_total_cache = total
            return total
        if self.procedure_id:
            valor = self.procedure.preco or Decimal(0)
            self._valor_total_cache = valor
            return valor
        self._valor_total_cache = Decimal(0)
        return self._valor_total_cache

    def get_valor_exibicao_agenda(self, *, retorno_elegivel=None) -> Decimal:
        """Taxa de consulta (local) + procedimentos, para exibição no calendário."""
        consulta = getattr(self, "consulta", None)
        if retorno_elegivel is None and consulta is not None and getattr(consulta, "retorno_gratuito", False):
            retorno_elegivel = True
        return calcular_valor_exibicao_agenda(
            self.valor_total,
            local_atendimento=getattr(self, "local_atendimento", None),
            consulta=consulta,
            procedure=self.procedure if self.procedure_id else None,
            procedure_id=self.procedure_id,
            appointment=self if retorno_elegivel is None else None,
            retorno_elegivel=retorno_elegivel,
        )


class AppointmentProcedure(LojaIsolationMixin, models.Model):
    """Procedimentos de um agendamento — permite N procedimentos por agendamento.
    Cada item tem sua duração (override opcional) e valor.
    """

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name="appointment_procedures",
        verbose_name="Agendamento",
    )
    procedure = models.ForeignKey(
        Procedure,
        on_delete=models.CASCADE,
        verbose_name="Procedimento",
    )
    duracao_minutos = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Duração (min)",
        help_text="Opcional. Se vazio, usa a duração cadastrada do procedimento.",
    )
    valor = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name="Valor (R$)",
        help_text="Opcional. Se vazio, usa o preço cadastrado do procedimento.",
    )
    ordem = models.PositiveSmallIntegerField(default=0, verbose_name="Ordem")

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        db_table = "clinica_beleza_appointment_procedures"
        ordering = ["ordem", "id"]
        verbose_name = "Procedimento do agendamento"
        verbose_name_plural = "Procedimentos do agendamento"

    def __str__(self):
        return f"{self.procedure.nome} ({self.get_duracao() or '?'} min)"

    def get_duracao(self) -> int:
        return self.duracao_minutos or self.procedure.duracao_minutos

    def get_valor(self):
        from decimal import Decimal
        return self.valor or self.procedure.preco or Decimal(0)




class BloqueioHorario(BloqueioAgendaBase):
    """Bloqueio de horário na agenda (herda de BloqueioAgendaBase)
    profissional=None = bloqueio geral (todos os profissionais).
    """

    professional = models.ForeignKey(
        Professional,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Profissional",
        help_text="Deixe vazio para bloqueio geral (todos)",
    )

    # Campos adicionais específicos (mantém compatibilidade)
    motivo = models.CharField(max_length=100, verbose_name="Motivo")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    # Aliases para compatibilidade
    @property
    def data_inicio_dt(self):
        """Retorna data_inicio como datetime para compatibilidade"""
        from datetime import datetime, time
        if self.horario_inicio:
            return datetime.combine(self.data_inicio, self.horario_inicio)
        return datetime.combine(self.data_inicio, time.min)

    @property
    def data_fim_dt(self):
        """Retorna data_fim como datetime para compatibilidade"""
        from datetime import datetime, time
        if self.horario_fim:
            return datetime.combine(self.data_fim, self.horario_fim)
        return datetime.combine(self.data_fim, time.max)

    class Meta(BloqueioAgendaBase.Meta):
        app_label = "clinica_beleza"
        verbose_name = "Bloqueio de Horário"
        verbose_name_plural = "Bloqueios de Horário"
        ordering = ["-data_inicio"]
        indexes = [
            models.Index(fields=["data_inicio", "data_fim"]),
            models.Index(fields=["professional", "data_inicio"]),
            models.Index(fields=["loja_id", "data_inicio"]),
        ]

    def __str__(self):
        return f"{self.motivo} ({self.data_inicio} - {self.data_fim})"

    def save(self, *args, **kwargs):
        # Sincronizar motivo com titulo
        if not self.titulo:
            self.titulo = self.motivo
        # Definir tipo padrão se não especificado
        if not self.tipo:
            self.tipo = "outros"
        super().save(*args, **kwargs)


