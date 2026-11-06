from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0103_payment_operador_caixa"),
    ]

    operations = [
        migrations.AddField(
            model_name="professional",
            name="intervalo_agenda_minutos",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                help_text="Passo da grade e dos horários deste profissional. Vazio usa 15 minutos.",
                verbose_name="Intervalo da agenda (min)",
            ),
        ),
    ]
