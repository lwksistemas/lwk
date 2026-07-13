"""Models — documentos clínicos."""
from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin


class DocumentTemplate(LojaIsolationMixin, models.Model):
    """Template reutilizável de documento clínico."""

    TIPO_CHOICES = [
        ("receituario", "Receituário"),
        ("pedido_exame", "Pedido de Exame"),
        ("atestado", "Atestado"),
        ("documento_personalizado", "Documento Personalizado"),
    ]
    professional = models.ForeignKey(
        "Professional", on_delete=models.CASCADE, related_name="document_templates",
        verbose_name="Profissional",
    )
    nome = models.CharField(max_length=200, verbose_name="Nome do template")
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, verbose_name="Tipo")
    conteudo = models.TextField(
        verbose_name="Conteúdo",
        help_text="Texto com placeholders: {{paciente_nome}}, {{data_atual}}, etc.",
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        db_table = "clinica_beleza_document_templates"
        ordering = ["-updated_at"]
        verbose_name = "Template de documento"
        verbose_name_plural = "Templates de documentos"

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"




class DocumentoClinico(LojaIsolationMixin, models.Model):
    """Documento clínico gerado durante uma consulta."""

    TIPO_CHOICES = DocumentTemplate.TIPO_CHOICES

    consulta = models.ForeignKey(
        "Consulta", on_delete=models.CASCADE, related_name="documentos",
        verbose_name="Consulta",
    )
    patient = models.ForeignKey(
        "Patient", on_delete=models.CASCADE, related_name="documentos_clinicos",
        verbose_name="Paciente",
    )
    professional = models.ForeignKey(
        "Professional", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="documentos_emitidos", verbose_name="Profissional",
    )
    template = models.ForeignKey(
        "DocumentTemplate", on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Template usado",
    )
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, verbose_name="Tipo")
    titulo = models.CharField(max_length=200, blank=True, default="", verbose_name="Título")
    conteudo = models.TextField(verbose_name="Conteúdo", help_text="Conteúdo final renderizado do documento.")
    created_at = models.DateTimeField(auto_now_add=True)
    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        db_table = "clinica_beleza_documentos_clinicos"
        ordering = ["-created_at"]
        verbose_name = "Documento clínico"
        verbose_name_plural = "Documentos clínicos"
        indexes = [
            models.Index(fields=["consulta", "-created_at"], name="cb_documento_consulta_idx"),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.patient.nome} ({self.created_at:%d/%m/%Y})"


# ═══════════════════════════════════════════════════════════════════════════════
# LOCAIS DE ATENDIMENTO — Locais onde consultas são realizadas
# ═══════════════════════════════════════════════════════════════════════════════

