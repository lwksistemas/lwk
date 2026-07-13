"""Models — pacientes e anamnese."""

from django.db import models

from agenda_base.models import ClienteBase
from core.mixins import LojaIsolationManager, LojaIsolationMixin


class Patient(ClienteBase):
    """Pacientes da clínica (herda de ClienteBase)"""

    allow_whatsapp = models.BooleanField(
        default=True,
        verbose_name="Permitir WhatsApp",
        help_text="Se desmarcado, o paciente não recebe mensagens por WhatsApp (LGPD).",
    )
    convenio = models.ForeignKey(
        "Convenio",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pacientes",
        verbose_name="Convênio padrão",
        help_text="Convênio sugerido ao agendar ou abrir consulta.",
    )
    foto_url = models.URLField(
        blank=True,
        default="",
        max_length=500,
        verbose_name="Foto",
        help_text="Foto de perfil do cliente (Cloudinary).",
    )

    class Meta(ClienteBase.Meta):
        app_label = "clinica_beleza"
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"
        ordering = ["nome"]

    def __str__(self):
        return self.nome




class PatientAnamnese(LojaIsolationMixin, models.Model):
    """Anamnese do cliente — histórico clínico persistente."""

    patient = models.OneToOneField(
        Patient,
        on_delete=models.CASCADE,
        related_name="anamnese",
        verbose_name="Cliente",
    )
    queixa_principal = models.TextField(blank=True, default="")
    historico_medico = models.TextField(blank=True, default="")
    medicamentos_uso = models.TextField(blank=True, default="")
    alergias = models.TextField(blank=True, default="")
    condicoes_clinicas = models.TextField(blank=True, default="")
    tipo_pele = models.CharField(max_length=100, blank=True, default="")
    pressao_arterial = models.CharField(max_length=20, blank=True, default="")
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    altura = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    observacoes = models.TextField(blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        db_table = "clinica_beleza_anamneses"
        verbose_name = "Anamnese do cliente"
        verbose_name_plural = "Anamneses dos clientes"

    def __str__(self):
        return f"Anamnese — {self.patient.nome}"


