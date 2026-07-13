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


def calcular_valor_exibicao_agenda(
    proc_total,
    *,
    local_atendimento=None,
    consulta=None,
    procedure=None,
    procedure_id=None,
    appointment=None,
) -> Decimal:
    """Valor exibido na agenda: taxa do local + procedimentos (sem duplicar legacy procedure)."""
    total_proc = Decimal(str(proc_total or 0))
    taxa = Decimal('0')
    if local_atendimento is not None:
        taxa = Decimal(str(getattr(local_atendimento, 'valor_consulta', 0) or 0))
    elif consulta is not None:
        vc = Decimal(str(getattr(consulta, 'valor_consulta', 0) or 0))
        if vc > 0:
            taxa = vc
    if appointment is not None and taxa > 0:
        from ..retorno_service import verificar_retorno_appointment
        if verificar_retorno_appointment(appointment).elegivel:
            taxa = Decimal('0')
    elif consulta is not None and getattr(consulta, 'retorno_gratuito', False):
        taxa = Decimal('0')

    if local_atendimento is not None:
        return taxa + total_proc
    if total_proc > 0:
        return total_proc
    if taxa > 0:
        return taxa
    if consulta is not None:
        vc = Decimal(str(getattr(consulta, 'valor_consulta', 0) or 0))
        if vc > 0:
            return vc
    if procedure_id and procedure is not None:
        return Decimal(str(getattr(procedure, 'preco', 0) or 0))
    return Decimal('0')


class Appointment(LojaIsolationMixin, models.Model):
    """Agendamentos"""
    STATUS_CHOICES = (
        ('CONFIRMED', 'Cliente presente'),
        ('CLIENT_CONFIRMED', 'Confirmado pelo WhatsApp'),
        ('PHONE_CONFIRMED', 'Confirmado por ligação'),
        ('PENDING', 'Aguardando confirmação'),  # legado — migrar para SCHEDULED
        ('SCHEDULED', 'Aguardando confirmação'),
        ('IN_PROGRESS', 'Em Atendimento'),
        ('COMPLETED', 'Consulta finalizada'),
        ('CANCELLED', 'Cancelado'),
        ('NO_SHOW', 'Faltou'),
    )

    date = models.DateTimeField(verbose_name="Data e Hora")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED', verbose_name="Status")
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
        Procedure, through='AppointmentProcedure',
        related_name='appointments_multi', blank=True,
        verbose_name="Procedimentos",
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Observações")
    convenio = models.ForeignKey(
        'Convenio',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agendamentos',
        verbose_name='Convênio',
        help_text='Convênio do atendimento (define preços dos procedimentos).',
    )
    nome_agenda = models.ForeignKey(
        NomeAgenda,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agendamentos',
        verbose_name='Nome da agenda',
    )
    local_atendimento = models.ForeignKey(
        LocalAtendimento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agendamentos',
        verbose_name='Local de atendimento',
    )
    retorno_procedure = models.ForeignKey(
        Procedure,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agendamentos_retorno',
        verbose_name='Retorno do procedimento',
        help_text='Indica retorno de acompanhamento deste procedimento (sem repetir cobrança da consulta).',
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

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date', 'status']),
            models.Index(fields=['professional', 'date']),
            models.Index(fields=['patient', 'date']),
            models.Index(fields=['loja_id', 'date']),
        ]

    def __str__(self):
        nomes = ', '.join(
            self.procedures.values_list('nome', flat=True)
        ) if self.procedures.exists() else (self.procedure.nome if self.procedure_id else '—')
        return f"{self.patient.nome} - {nomes} - {self.date.strftime('%d/%m/%Y %H:%M')}"

    def get_duracao_efetiva(self) -> int:
        """Duração efetiva: manual > max(procedimentos, tempo consulta do profissional)."""
        from ..duracao_consulta import calcular_duracao_efetiva_agendamento

        appointment_procedures = list(
            self.appointment_procedures.select_related('procedure').all()
        )
        procedure_principal = self.procedure if self.procedure_id else None
        return calcular_duracao_efetiva_agendamento(
            duracao_manual=self.duracao_minutos,
            professional=self.professional,
            local_atendimento=self.local_atendimento,
            appointment_procedures=appointment_procedures if appointment_procedures else None,
            procedure_principal=procedure_principal,
        )

    @property
    def valor_total(self):
        """Valor total: soma dos preços de todos os procedimentos."""
        from decimal import Decimal
        total = sum(
            (ap.valor or ap.procedure.preco or Decimal('0'))
            for ap in self.appointment_procedures.select_related('procedure').all()
        )
        if total > 0:
            return total
        if self.procedure_id:
            return self.procedure.preco or Decimal('0')
        return Decimal('0')

    def get_valor_exibicao_agenda(self) -> Decimal:
        """Taxa de consulta (local) + procedimentos, para exibição no calendário."""
        consulta = getattr(self, 'consulta', None)
        return calcular_valor_exibicao_agenda(
            self.valor_total,
            local_atendimento=getattr(self, 'local_atendimento', None),
            consulta=consulta,
            procedure=self.procedure if self.procedure_id else None,
            procedure_id=self.procedure_id,
            appointment=self,
        )


class AppointmentProcedure(LojaIsolationMixin, models.Model):
    """
    Procedimentos de um agendamento — permite N procedimentos por agendamento.
    Cada item tem sua duração (override opcional) e valor.
    """
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name='appointment_procedures',
        verbose_name='Agendamento',
    )
    procedure = models.ForeignKey(
        Procedure,
        on_delete=models.CASCADE,
        verbose_name='Procedimento',
    )
    duracao_minutos = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name='Duração (min)',
        help_text='Opcional. Se vazio, usa a duração cadastrada do procedimento.',
    )
    valor = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name='Valor (R$)',
        help_text='Opcional. Se vazio, usa o preço cadastrado do procedimento.',
    )
    ordem = models.PositiveSmallIntegerField(default=0, verbose_name='Ordem')

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_appointment_procedures'
        ordering = ['ordem', 'id']
        verbose_name = 'Procedimento do agendamento'
        verbose_name_plural = 'Procedimentos do agendamento'

    def __str__(self):
        return f"{self.procedure.nome} ({self.get_duracao() or '?'} min)"

    def get_duracao(self) -> int:
        return self.duracao_minutos or self.procedure.duracao_minutos

    def get_valor(self):
        from decimal import Decimal
        return self.valor or self.procedure.preco or Decimal('0')




class BloqueioHorario(BloqueioAgendaBase):
    """
    Bloqueio de horário na agenda (herda de BloqueioAgendaBase)
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
            models.Index(fields=['data_inicio', 'data_fim']),
            models.Index(fields=['professional', 'data_inicio']),
            models.Index(fields=['loja_id', 'data_inicio']),
        ]

    def __str__(self):
        return f"{self.motivo} ({self.data_inicio} - {self.data_fim})"
    
    def save(self, *args, **kwargs):
        # Sincronizar motivo com titulo
        if not self.titulo:
            self.titulo = self.motivo
        # Definir tipo padrão se não especificado
        if not self.tipo:
            self.tipo = 'outros'
        super().save(*args, **kwargs)


