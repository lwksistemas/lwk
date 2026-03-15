# Migration para criar schema 'suporte' no PostgreSQL (produção)
# Em SQLite (desenvolvimento), esta migration é no-op

from django.db import migrations


def create_schema_postgres(apps, schema_editor):
    """Cria schema suporte no PostgreSQL. Ignora em SQLite."""
    from django.db import connection
    engine = connection.settings_dict.get('ENGINE', '')
    if 'postgresql' in engine:
        with connection.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS suporte")


def noop(apps, schema_editor):
    """Operação reversa: schema não é removido (dados seriam perdidos)."""
    pass


class Migration(migrations.Migration):
    """Garante que o schema suporte exista antes de criar tabelas."""

    initial = True
    run_before = [('suporte', '0001_initial')]

    dependencies = []

    operations = [
        migrations.RunPython(create_schema_postgres, noop, elidable=True),
    ]
