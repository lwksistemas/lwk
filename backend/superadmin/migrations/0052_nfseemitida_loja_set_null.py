# Generated manually
# Altera NFSeEmitida.loja de CASCADE para SET_NULL
# Preserva histórico de notas fiscais mesmo quando a loja é excluída

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0051_googlecalendar_loja_fk_cascade'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nfseemitida',
            name='loja',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='nfse_emitidas',
                to='superadmin.loja',
            ),
        ),
    ]
