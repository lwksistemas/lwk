# Tempo da consulta fica em Local de Atendimento, não no profissional.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0044_professional_tempo_consulta"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="professional",
            name="tempo_consulta_minutos",
        ),
    ]
