# Generated manually — default de horario_envio alinhado à madrugada BRT.

import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0061_loja_colunas_estoque"),
    ]

    operations = [
        migrations.AlterField(
            model_name="configuracaobackup",
            name="horario_envio",
            field=models.TimeField(
                default=datetime.time(0, 0),
                help_text="Slot noturno (00:00–04:45 BRT) atribuído pelo sistema por loja",
            ),
        ),
    ]
