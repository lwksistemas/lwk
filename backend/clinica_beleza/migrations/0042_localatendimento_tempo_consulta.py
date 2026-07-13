from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0041_appointment_local_atendimento"),
    ]

    operations = [
        migrations.AddField(
            model_name="localatendimento",
            name="tempo_consulta_minutos",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Duração padrão da consulta neste local (ex.: 40 minutos).",
                null=True,
                verbose_name="Tempo da consulta (minutos)",
            ),
        ),
    ]
