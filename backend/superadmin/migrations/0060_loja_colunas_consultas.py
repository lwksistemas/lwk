from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0059_loja_cor_fundo_pagina'),
    ]

    operations = [
        migrations.AddField(
            model_name='loja',
            name='colunas_consultas',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Colunas visíveis na listagem de Consultas (clínica). Vazio = padrão sem AGENDA.',
            ),
        ),
    ]
