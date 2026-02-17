"""
Modelo opcional para regras configuráveis pelo admin (ativar/desativar por evento).
O motor principal usa regras em código; este modelo permite expandir no futuro.
"""
from django.db import models


class RegraAutomatica(models.Model):
    nome = models.CharField(max_length=100)
    ativa = models.BooleanField(default=True)
    evento = models.CharField(max_length=50)
    acao = models.CharField(max_length=50, help_text="Identificador da ação em código")

    class Meta:
        app_label = 'rules'
        verbose_name = 'Regra automática'
        verbose_name_plural = 'Regras automáticas'

    def __str__(self):
        return self.nome
