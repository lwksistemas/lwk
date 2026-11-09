import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0105_simulacao_estetica_config"),
    ]

    operations = [
        migrations.CreateModel(
            name="SimulacaoConsulta",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("modo", models.CharField(max_length=12)),
                ("parametro", models.CharField(blank=True, default="", max_length=40)),
                ("intensidade", models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ("quantidade", models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ("status", models.CharField(default="processando", max_length=16)),
                ("task_id", models.CharField(blank=True, default="", max_length=180)),
                ("resultado_url", models.URLField(blank=True, default="", max_length=500)),
                ("resultado_json", models.JSONField(blank=True, default=dict)),
                ("erro", models.TextField(blank=True, default="")),
                ("ilustrativa", models.BooleanField(default=True)),
                ("ciencia_visual", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "consulta",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="simulacoes",
                        to="clinica_beleza.consulta",
                    ),
                ),
                (
                    "foto",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="simulacoes",
                        to="clinica_beleza.pacientefotoacompanhamento",
                    ),
                ),
            ],
            options={
                "verbose_name": "Simulação da consulta",
                "db_table": "clinica_beleza_simulacao_consulta",
                "ordering": ["-created_at"],
            },
        ),
    ]
