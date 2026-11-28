"""Novidades e promoções exibidas no Agendamento Online (por loja)."""
from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin


class NovidadeConfig(LojaIsolationMixin, models.Model):
    """Configuração do carrossel de novidades da clínica."""

    ativo = models.BooleanField(
        default=True,
        help_text="Exibir o carrossel de novidades na página pública.",
    )
    intervalo_carrossel = models.PositiveSmallIntegerField(
        default=5,
        help_text="Segundos entre os slides do carrossel (3 a 30).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = "clinica_beleza_novidade_config"
        verbose_name = "Configuração de novidades"
        constraints = [
            models.UniqueConstraint(fields=["loja_id"], name="uniq_novidade_config_loja"),
        ]

    def __str__(self):
        return f"Novidades config (loja_id={self.loja_id}, ativo={self.ativo})"


class Novidade(LojaIsolationMixin, models.Model):
    """Slide de novidade/promoção da clínica."""

    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, default="")
    imagem_url = models.URLField(max_length=500, blank=True, default="")
    selo = models.CharField(
        max_length=40,
        blank=True,
        default="Novidades",
        help_text="Etiqueta no canto do card, ex.: Novidades, Promoção.",
    )
    condicao_especial = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Texto do destaque de preço/oferta.",
    )
    preco_de = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
    )
    preco_por = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
    )
    botao_texto = models.CharField(max_length=80, blank=True, default="Agende agora")
    botao_url = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Link do botão. Vazio = inicia o agendamento na mesma página.",
    )
    beneficios = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de textos curtos exibidos no slide.",
    )
    ordem = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)
    data_inicio = models.DateField(null=True, blank=True)
    data_fim = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = "clinica_beleza_novidade"
        ordering = ["ordem", "id"]
        verbose_name = "Novidade"
        verbose_name_plural = "Novidades"

    def __str__(self):
        return self.titulo
