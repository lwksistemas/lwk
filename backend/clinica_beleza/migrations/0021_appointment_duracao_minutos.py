from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0020_consulta_status_scheduled"),
    ]

    operations = [
        migrations.AddField(
            model_name="appointment",
            name="duracao_minutos",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Opcional. Se vazio, usa a duração cadastrada do procedimento.",
                null=True,
                verbose_name="Duração efetiva (min)",
            ),
        ),
    ]
