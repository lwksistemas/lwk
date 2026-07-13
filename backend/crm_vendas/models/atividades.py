from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin

from .contas import Conta
from .leads import Lead
from .oportunidades import Oportunidade


class Atividade(LojaIsolationMixin, models.Model):
    """Atividade (tarefa, ligação, reunião, email)."""

    TIPO_CHOICES = [
        ("call", "Ligação"),
        ("meeting", "Reunião"),
        ("email", "Email"),
        ("task", "Tarefa"),
    ]

    titulo = models.CharField(max_length=255)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default="task")
    oportunidade = models.ForeignKey(
        Oportunidade,
        on_delete=models.CASCADE,
        related_name="atividades",
        null=True,
        blank=True,
    )
    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name="atividades",
        null=True,
        blank=True,
    )
    conta = models.ForeignKey(
        Conta,
        on_delete=models.CASCADE,
        related_name="atividades",
        null=True,
        blank=True,
        help_text="Conta (empresa) vinculada a esta atividade",
    )
    data = models.DateTimeField()
    duracao_minutos = models.PositiveIntegerField(
        default=60,
        help_text="Duração estimada da atividade em minutos",
    )
    concluido = models.BooleanField(default=False)
    lembrete_whatsapp = models.BooleanField(
        default=False,
        help_text="Enviar lembretes automáticos por WhatsApp 24h e 2h antes da atividade",
    )
    lembrete_whatsapp_telefone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Número para lembretes automáticos (ex: 5511999999999)",
    )
    lembrete_24h_enviado_em = models.DateTimeField(null=True, blank=True)
    lembrete_2h_enviado_em = models.DateTimeField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    google_event_id = models.CharField(max_length=255, blank=True, null=True, help_text="ID do evento no Google Calendar (sincronização)")
    criado_por_vendedor_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Vendedor que criou/importou esta atividade (órfã). Null = proprietário. Usado para filtrar calendário por vendedor.",
    )

    objects = LojaIsolationManager()

    class Meta:
        db_table = "crm_vendas_atividade"
        ordering = ["data"]
        verbose_name = "Atividade"
        verbose_name_plural = "Atividades"
        indexes = [
            models.Index(fields=["loja_id", "data"], name="crm_ativ_loja_data_idx"),
            models.Index(fields=["loja_id", "concluido"], name="crm_ativ_loja_concl_idx"),
            models.Index(fields=["loja_id", "oportunidade"], name="crm_ativ_loja_opor_idx"),
            models.Index(fields=["loja_id", "lead"], name="crm_ativ_loja_lead_idx"),
            models.Index(fields=["loja_id", "conta"], name="crm_ativ_loja_conta_idx"),
            models.Index(fields=["loja_id", "data", "concluido"], name="crm_ativ_loja_data_concl_idx"),
        ]

    def __str__(self):
        return f"{self.titulo} ({self.get_tipo_display()})"

