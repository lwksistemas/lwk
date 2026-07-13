import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0040_nome_agenda"),
    ]

    operations = [
        migrations.AddField(
            model_name="appointment",
            name="local_atendimento",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="agendamentos",
                to="clinica_beleza.localatendimento",
                verbose_name="Local de atendimento",
            ),
        ),
    ]
