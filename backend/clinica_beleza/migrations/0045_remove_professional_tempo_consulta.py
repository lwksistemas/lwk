# Tempo da consulta fica em Local de Atendimento, não no profissional.

from django.db import migrations


def drop_professional_tempo_column(apps, schema_editor):
    """Remove coluna obsoleta se existir (PostgreSQL)."""
    from django.db import connection

    engine = connection.settings_dict.get('ENGINE', '')
    if 'postgresql' not in engine:
        return
    with connection.cursor() as cursor:
        cursor.execute(
            """
            ALTER TABLE clinica_beleza_professional
            DROP COLUMN IF EXISTS tempo_consulta_minutos
            """
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_beleza', '0044_professional_tempo_consulta'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(drop_professional_tempo_column, noop, elidable=True),
            ],
            state_operations=[
                migrations.RemoveField(
                    model_name='professional',
                    name='tempo_consulta_minutos',
                ),
            ],
        ),
    ]
