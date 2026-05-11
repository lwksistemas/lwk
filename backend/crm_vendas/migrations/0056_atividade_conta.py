# Generated manually
# Adiciona campo conta (empresa) na Atividade para vincular interações a contas

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0055_produtoservico_recorrencia'),
    ]

    operations = [
        migrations.AddField(
            model_name='atividade',
            name='conta',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='atividades',
                to='crm_vendas.conta',
                help_text='Conta (empresa) vinculada a esta atividade',
            ),
        ),
        migrations.AddIndex(
            model_name='atividade',
            index=models.Index(fields=['loja_id', 'conta'], name='crm_ativ_loja_conta_idx'),
        ),
    ]
