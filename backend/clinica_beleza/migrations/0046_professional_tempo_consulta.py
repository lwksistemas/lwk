from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0045_remove_professional_tempo_consulta"),
    ]

    operations = [
        migrations.AddField(
            model_name="professional",
            name="tempo_consulta_minutos",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                verbose_name="Tempo da consulta (min)",
                help_text="Duração padrão da consulta deste profissional. Se os procedimentos somarem mais tempo, prevalece a soma dos procedimentos.",
            ),
        ),
    ]
