"""Models — pacientes e anamnese."""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from agenda_base.models import ClienteBase
from core.mixins import LojaIsolationManager, LojaIsolationMixin


class Patient(ClienteBase):
    """Pacientes da clínica (herda de ClienteBase)"""

    SEXO_CHOICES = [
        ("M", "Masculino"),
        ("F", "Feminino"),
    ]

    # Política de prazo de pagamento (configurada só pelo administrador no prontuário).
    # Define o vencimento das consultas recebidas "a prazo" para este paciente.
    PRAZO_MODO_SEM = ""
    PRAZO_MODO_DIAS_APOS = "DIAS_APOS"
    PRAZO_MODO_DIA_FIXO = "DIA_FIXO"
    PRAZO_MODO_CHOICES = [
        (PRAZO_MODO_SEM, "Sem prazo configurado"),
        (PRAZO_MODO_DIAS_APOS, "Dias após finalizar a consulta"),
        (PRAZO_MODO_DIA_FIXO, "Dia fixo do mês"),
    ]
    prazo_pagamento_modo = models.CharField(
        max_length=20,
        blank=True,
        default=PRAZO_MODO_SEM,
        choices=PRAZO_MODO_CHOICES,
        verbose_name="Modo do prazo de pagamento",
        help_text=(
            "Como calcular o vencimento das consultas a prazo deste paciente. "
            "Vazio = paciente não pode receber a prazo."
        ),
    )
    prazo_pagamento_dias = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(365)],
        verbose_name="Dias após finalizar",
        help_text="Usado quando o modo é 'Dias após finalizar' (ex.: 10).",
    )
    prazo_pagamento_dia_mes = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(28)],
        verbose_name="Dia fixo do mês",
        help_text="Usado quando o modo é 'Dia fixo do mês' (1 a 28). Vence sempre no mês seguinte.",
    )
    sexo = models.CharField(
        max_length=1,
        blank=True,
        default="",
        choices=SEXO_CHOICES,
        verbose_name="Sexo",
        help_text="Usado na identificação do paciente na prescrição digital (Memed).",
    )
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
        help_text="Foto de perfil do cliente (servidor de mídia).",
    )

    class Meta(ClienteBase.Meta):
        app_label = "clinica_beleza"
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    @property
    def tem_prazo_pagamento(self) -> bool:
        """True se o paciente tem uma política de prazo válida para receber a prazo."""
        if self.prazo_pagamento_modo == self.PRAZO_MODO_DIAS_APOS:
            return bool(self.prazo_pagamento_dias)
        if self.prazo_pagamento_modo == self.PRAZO_MODO_DIA_FIXO:
            return bool(self.prazo_pagamento_dia_mes)
        return False




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
    tipo_pele = models.TextField(blank=True, default="")
    pressao_arterial = models.TextField(blank=True, default="")
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


