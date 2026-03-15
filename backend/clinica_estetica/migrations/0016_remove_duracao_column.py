# Remove coluna obsoleta 'duracao' - modelo usa apenas duracao_minutos (ServicoBase)
# A coluna duracao causa IntegrityError ao inserir pois é NOT NULL e não é mais preenchida

from django.db import migrations


def remove_duracao_column(apps, schema_editor):
    """Remove coluna duracao se existir (PostgreSQL). No-op em SQLite."""
    from django.db import connection
    engine = connection.settings_dict.get('ENGINE', '')
    if 'postgresql' in engine:
        with connection.cursor() as cursor:
            cursor.execute("""
                ALTER TABLE clinica_procedimentos
                DROP COLUMN IF EXISTS duracao
            """)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_estetica', '0015_add_duracao_minutos'),
    ]

    operations = [
        migrations.RunPython(remove_duracao_column, noop, elidable=True),
    ]
