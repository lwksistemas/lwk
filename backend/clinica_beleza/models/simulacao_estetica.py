"""Chave de simulação estética da própria clínica."""
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
