"""Chave e resultados de simulação estética da própria clínica."""
from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin


class SimulacaoEsteticaConfig(LojaIsolationMixin, models.Model):
    """Uma configuração por loja. A chave não é compartilhada entre clínicas."""

    PROVEDOR_YOUCAM = "youcam"
    PROVEDOR_CHOICES = [
        (PROVEDOR_YOUCAM, "YouCam API"),
    ]

    provedor = models.CharField(
        max_length=20,
        choices=PROVEDOR_CHOICES,
        default=PROVEDOR_YOUCAM,
    )
    api_key = models.TextField(blank=True, default="")
    ativa = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = "clinica_beleza_simulacao_estetica_config"
        verbose_name = "Simulação estética"
        constraints = [
            models.UniqueConstraint(fields=["loja_id"], name="uniq_simulacao_estetica_loja"),
        ]

    def __str__(self):
        return f"Simulação estética (loja_id={self.loja_id})"


class SimulacaoConsulta(LojaIsolationMixin, models.Model):
    """Resultado ilustrativo ligado à consulta. Não baixa estoque nem substitui o termo."""

    MODO_ANALISE = "analise"
    MODO_PELE = "pele"
    MODO_ROSTO = "rosto"
    MODO_CORPO = "corpo"
    STATUS_PROCESSANDO = "processando"
    STATUS_PRONTA = "pronta"
    STATUS_ERRO = "erro"

    consulta = models.ForeignKey(
        "clinica_beleza.Consulta",
        on_delete=models.CASCADE,
        related_name="simulacoes",
    )
    foto = models.ForeignKey(
        "clinica_beleza.PacienteFotoAcompanhamento",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="simulacoes",
    )
    modo = models.CharField(max_length=12)
    parametro = models.CharField(max_length=40, blank=True, default="")
    intensidade = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    quantidade = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=16, default=STATUS_PROCESSANDO)
    task_id = models.CharField(max_length=180, blank=True, default="")
    resultado_url = models.URLField(max_length=500, blank=True, default="")
    resultado_json = models.JSONField(default=dict, blank=True)
    erro = models.TextField(blank=True, default="")
    ilustrativa = models.BooleanField(default=True)
    ciencia_visual = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = "clinica_beleza_simulacao_consulta"
        ordering = ["-created_at"]
        verbose_name = "Simulação da consulta"

    def __str__(self):
        return f"Simulação {self.modo} consulta {self.consulta_id}"
