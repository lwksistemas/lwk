"""Configuração e vínculos do Agendamento Online (Clínica da Beleza)."""
from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin


class AgendamentoOnlineConfig(LojaIsolationMixin, models.Model):
    """Uma configuração por loja."""

    MODO_AUTOMATICO = "automatico"
    MODO_SECRETARIA = "secretaria"
    MODO_CHOICES = (
        (MODO_AUTOMATICO, "Confirmação automática"),
        (MODO_SECRETARIA, "Aprovação pela secretaria"),
    )

    ativo = models.BooleanField(default=False)
    antecedencia_minima_horas = models.PositiveIntegerField(
        default=2,
        help_text="Horas mínimas entre agora e o início do horário.",
    )
    dias_futuros = models.PositiveIntegerField(
        default=30,
        help_text="Quantos dias à frente o cliente pode ver no calendário.",
    )
    permitir_mesmo_dia = models.BooleanField(default=True)
    intervalo_slots_minutos = models.PositiveIntegerField(default=30)
    modo_confirmacao = models.CharField(
        max_length=20, choices=MODO_CHOICES, default=MODO_AUTOMATICO,
    )
    permitir_cancelamento_cliente = models.BooleanField(default=True)
    permitir_reagendamento_cliente = models.BooleanField(default=True)
    prazo_cancelamento_horas = models.PositiveIntegerField(
        default=24,
        help_text="Horas mínimas antes do horário para cancelar/reagendar.",
    )
    reserva_pendente_minutos = models.PositiveIntegerField(
        default=120,
        help_text="Quanto tempo um pedido aguardando aprovação reserva o horário.",
    )

    # Comunicação
    enviar_confirmacao = models.BooleanField(default=True)
    enviar_lembrete = models.BooleanField(default=True)
    enviar_cancelamento = models.BooleanField(default=True)
    enviar_reagendamento = models.BooleanField(default=True)
    notificar_secretaria = models.BooleanField(default=True)
    botao_whatsapp_ativo = models.BooleanField(default=True)
    whatsapp_secretaria = models.CharField(
        max_length=20, blank=True, default="",
        help_text="Número específico da secretaria (opcional). Vazio = número da clínica.",
    )

    # Página pública
    nome_publico = models.CharField(max_length=200, blank=True, default="")
    texto_apresentacao = models.TextField(blank=True, default="")
    logo_url = models.URLField(max_length=500, blank=True, default="")
    banner_url = models.URLField(max_length=500, blank=True, default="")
    cor_primaria = models.CharField(max_length=20, blank=True, default="")
    cor_secundaria = models.CharField(max_length=20, blank=True, default="")
    endereco_publico = models.CharField(max_length=300, blank=True, default="")
    telefone_publico = models.CharField(max_length=30, blank=True, default="")
    politica_privacidade = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = "clinica_beleza_agendamento_online_config"
        verbose_name = "Configuração do agendamento online"
        constraints = [
            models.UniqueConstraint(fields=["loja_id"], name="uniq_agendamento_online_config_loja"),
        ]

    def __str__(self):
        return f"Agendamento online (loja_id={self.loja_id}, ativo={self.ativo})"


class AgendamentoOnlineProfissional(LojaIsolationMixin, models.Model):
    """Profissional liberado (ou não) no agendamento online."""

    professional = models.OneToOneField(
        "clinica_beleza.Professional",
        on_delete=models.CASCADE,
        related_name="agendamento_online",
    )
    liberado = models.BooleanField(default=False)
    bloqueado_temporariamente = models.BooleanField(default=False)
    usar_horarios_exclusivos = models.BooleanField(
        default=False,
        help_text="Se falso, usa o horário de trabalho cadastrado (menos intervalo).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = "clinica_beleza_agendamento_online_profissional"
        verbose_name = "Profissional no agendamento online"

    def __str__(self):
        return f"Online prof={self.professional_id} liberado={self.liberado}"


class AgendamentoOnlineHorario(LojaIsolationMixin, models.Model):
    """Período exclusivo de agendamento online (não altera o horário de trabalho)."""

    vinculo = models.ForeignKey(
        AgendamentoOnlineProfissional,
        on_delete=models.CASCADE,
        related_name="horarios",
    )
    dia_semana = models.PositiveSmallIntegerField(
        help_text="0=segunda … 6=domingo",
    )
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()
    ativo = models.BooleanField(default=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = "clinica_beleza_agendamento_online_horario"
        verbose_name = "Horário online do profissional"
        ordering = ["dia_semana", "hora_inicio"]

    def __str__(self):
        return f"dia={self.dia_semana} {self.hora_inicio}-{self.hora_fim}"


class AgendamentoOnlineProcedimento(LojaIsolationMixin, models.Model):
    """Procedimento liberado no agendamento online."""

    procedure = models.OneToOneField(
        "clinica_beleza.Procedure",
        on_delete=models.CASCADE,
        related_name="agendamento_online",
    )
    liberado = models.BooleanField(default=True)
    exibir_valor = models.BooleanField(default=True)
    profissionais = models.ManyToManyField(
        "clinica_beleza.Professional",
        blank=True,
        related_name="procedimentos_online",
        help_text="Vazio = todos os profissionais liberados online.",
    )
    ordem = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = "clinica_beleza_agendamento_online_procedimento"
        verbose_name = "Procedimento no agendamento online"
        ordering = ["ordem", "id"]

    def __str__(self):
        return f"Online proc={self.procedure_id} liberado={self.liberado}"
