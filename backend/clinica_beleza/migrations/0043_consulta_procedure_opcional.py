# Generated manually — procedimento opcional em consultas avulsas (orçamento, representante).

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0042_localatendimento_tempo_consulta"),
    ]

    operations = [
        migrations.AlterField(
            model_name="consulta",
            name="procedure",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="consultas",
                to="clinica_beleza.procedure",
                verbose_name="Procedimento",
            ),
        ),
    ]
