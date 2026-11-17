from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("salao_cabeleireiro", "0016_categoria_procedimentos"),
    ]

    operations = [
        migrations.AddField(
            model_name="profissional",
            name="intervalo_agenda_minutos",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Passo entre um horário e o outro na agenda. Vazio usa 15 minutos.",
                null=True,
                verbose_name="Intervalo por atendimento (min)",
            ),
        ),
    ]
