from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("salao_cabeleireiro", "0002_recebimento"),
    ]

    operations = [
        migrations.AddField(
            model_name="salaoconfig",
            name="enviar_cancelamento",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="salaoconfig",
            name="enviar_confirmacao",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="salaoconfig",
            name="enviar_lembrete",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="salaoconfig",
            name="enviar_reagendamento",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="salaoconfig",
            name="lembrete_horas",
            field=models.PositiveSmallIntegerField(default=24),
        ),
    ]
