"""Campos ISSNet padrão Nacional (DPS) — corrige migration 0027 mal numerada.

A migration antiga `0027_crmconfig_issnet_nacional` dependia de 0026 e criava
um segundo leaf no grafo (conflito com 0072). Este arquivo a substitui.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0072_crmconfig_nacional_codigo_municipio"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="crmconfig",
                    name="issnet_usar_padrao_nacional",
                    field=models.BooleanField(
                        default=False,
                        help_text="Se True, emite via padrão Nacional ISSNet (DPS). Se False, usa ABRASF até 03/08/2026.",
                        verbose_name="Usar padrão Nacional (DPS)",
                    ),
                ),
                migrations.AddField(
                    model_name="crmconfig",
                    name="codigo_tributacao_nacional",
                    field=models.CharField(
                        blank=True,
                        default="",
                        help_text="Código de 6 dígitos do serviço no padrão Nacional (ex: 140100 para item 14.01).",
                        max_length=10,
                        verbose_name="Código de Tributação Nacional (cTribNac)",
                    ),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE crm_vendas_crmconfig "
                        "ADD COLUMN IF NOT EXISTS issnet_usar_padrao_nacional "
                        "boolean NOT NULL DEFAULT false;"
                    ),
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE crm_vendas_crmconfig "
                        "ADD COLUMN IF NOT EXISTS codigo_tributacao_nacional "
                        "varchar(10) NOT NULL DEFAULT '';"
                    ),
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
        ),
    ]
