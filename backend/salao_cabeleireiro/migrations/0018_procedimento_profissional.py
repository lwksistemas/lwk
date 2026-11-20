from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("salao_cabeleireiro", "0017_intervalo_atendimento"),
    ]

    operations = [
        migrations.AddField(
            model_name="agendamentoprocedimento",
            name="profissional",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.PROTECT,
                related_name="procedimentos_do_horario",
                to="salao_cabeleireiro.profissional",
                verbose_name="Profissional",
            ),
        ),
    ]
