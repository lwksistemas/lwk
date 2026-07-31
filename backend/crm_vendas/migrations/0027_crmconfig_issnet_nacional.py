"""Adiciona campos para ISSNet padrão Nacional (DPS/RTC).

Novos campos:
- issnet_usar_padrao_nacional: flag para ativar novo padrão
- codigo_tributacao_nacional: cTribNac (6 dígitos)
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0026_add_numero_proposta"),
    ]

    operations = [
        migrations.AddField(
            model_name="crmconfig",
            name="issnet_usar_padrao_nacional",
            field=models.BooleanField(
                default=False,
                verbose_name="Usar padrão Nacional (DPS)",
                help_text="Se True, emite via padrão Nacional ISSNet (DPS). Se False, usa ABRASF até 03/08/2026.",
            ),
        ),
        migrations.AddField(
            model_name="crmconfig",
            name="codigo_tributacao_nacional",
            field=models.CharField(
                max_length=10,
                blank=True,
                default="",
                verbose_name="Código de Tributação Nacional (cTribNac)",
                help_text="Código de 6 dígitos do serviço no padrão Nacional (ex: 140100 para item 14.01).",
            ),
        ),
    ]
