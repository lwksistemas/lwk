# Generated manually — recorrência semestral (6 meses) em produto/serviço + financeiro

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0070_lancamento_data_pagamento_index"),
    ]

    operations = [
        migrations.AlterField(
            model_name="produtoservico",
            name="recorrencia",
            field=models.CharField(
                choices=[
                    ("unico", "Único (adesão/implantação)"),
                    ("mensal", "Mensal"),
                    ("trimestral", "Trimestral"),
                    ("semestral", "Semestral"),
                    ("anual", "Anual"),
                ],
                default="unico",
                help_text="Tipo de cobrança: único (adesão) ou recorrente (mensal, trimestral, semestral, anual)",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="recorrenciafinanceirocrm",
            name="frequencia",
            field=models.CharField(
                choices=[
                    ("mensal", "Mensal"),
                    ("trimestral", "Trimestral"),
                    ("semestral", "Semestral"),
                    ("anual", "Anual"),
                ],
                default="mensal",
                max_length=12,
                verbose_name="Frequência",
            ),
        ),
    ]
