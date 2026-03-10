# Generated manually to add duracao_minutos field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_estetica', '0014_add_comissao_percentual'),
    ]

    operations = [
        migrations.AddField(
            model_name='procedimento',
            name='duracao_minutos',
            field=models.IntegerField(
                default=30,
                verbose_name='Duração (minutos)'
            ),
        ),
    ]
