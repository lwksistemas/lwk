"""Resultado de exame importado na consulta de retorno."""
from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin

from .consultas import Consulta, PrescricaoMemed
from .documentos import DocumentoClinico
from .patients import Patient


class ResultadoExamePaciente(LojaIsolationMixin, models.Model):
    """PDF do laboratório vinculado ao paciente e à consulta em que foi importado."""

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="resultados_exame",
        verbose_name="Paciente",
    )
    consulta = models.ForeignKey(
        Consulta,
        on_delete=models.CASCADE,
        related_name="resultados_exame",
        verbose_name="Consulta do retorno",
        help_text="Consulta em que o profissional importou o PDF.",
    )
    consulta_origem = models.ForeignKey(
        Consulta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resultados_exame_origem",
        verbose_name="Consulta do pedido",
    )
    documento_origem = models.ForeignKey(
        DocumentoClinico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resultados_exame",
        verbose_name="Pedido de exame (documento)",
    )
    prescricao_origem = models.ForeignKey(
        PrescricaoMemed,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resultados_exame",
        verbose_name="Pedido de exame (Memed)",
    )
    pdf_url = models.URLField(max_length=500, blank=True, default="")
    nome_arquivo = models.CharField(max_length=255, blank=True, default="")
    texto_extraido = models.TextField(blank=True, default="")
    marcadores = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de biomarcadores com valor, faixa e status da sugestão.",
    )
    sugestao_texto = models.TextField(
        blank=True,
        default="",
        help_text="Texto de apoio gerado pelas faixas de referência (não é diagnóstico).",
    )
    aviso_cadastro = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Aviso quando falta sexo ou data de nascimento no cadastro.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        db_table = "clinica_beleza_resultado_exame"
        ordering = ["-created_at"]
        verbose_name = "Resultado de exame"
        verbose_name_plural = "Resultados de exame"
        indexes = [
            models.Index(fields=["patient", "created_at"], name="cb_res_exame_pac_dt_idx"),
            models.Index(fields=["consulta"], name="cb_res_exame_cons_idx"),
        ]

    def __str__(self):
        return f"Resultado exame paciente {self.patient_id} consulta {self.consulta_id}"
