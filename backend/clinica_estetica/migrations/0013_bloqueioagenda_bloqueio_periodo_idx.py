# Índice composto para queries de bloqueios por período (loja + ativo + datas)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_estetica', '0012_remove_horariotrabalhoprofissional_clinica_hor_profissi_6a0b0d_idx_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='bloqueioagenda',
            index=models.Index(
                fields=['loja_id', 'is_active', 'data_inicio', 'data_fim'],
                name='bloqueio_periodo_idx',
            ),
        ),
    ]
