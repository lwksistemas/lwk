# Sincronização offline: version e updated_by_id para conflito inteligente

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_beleza', '0004_add_loja_isolation'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='version',
            field=models.PositiveIntegerField(default=1, verbose_name='Versão'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='updated_by_id',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Atualizado por (user id)'),
        ),
    ]
