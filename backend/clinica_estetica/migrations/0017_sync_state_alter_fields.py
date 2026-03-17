# Sincroniza estado das migrações com o banco (RemoveField duracao já foi aplicado em 0016)
# AlterField são apenas metadados (verbose_name, help_text)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_estetica', '0016_remove_duracao_column'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name='procedimento',
                    name='duracao',
                ),
            ],
            database_operations=[],
        ),
    ]
