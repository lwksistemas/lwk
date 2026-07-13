# HeroSection.imagem foi criado só via SQL em 0004 (não no estado das migrações).
# RemoveField falharia com KeyError; usamos SQL idempotente no banco.

import contextlib

from django.db import migrations


def drop_hero_imagem_column(apps, schema_editor):
    from django.db import connection

    table = "homepage_hero_section"
    column = "imagem"
    with connection.cursor() as cursor:
        if connection.vendor == "sqlite":
            cursor.execute(f'PRAGMA table_info("{table}")')
            if not any(row[1] == column for row in cursor.fetchall()):
                return
            # SQLite 3.35+ suporta DROP COLUMN; versões antigas ignoram silenciosamente via exceção
            with contextlib.suppress(Exception):
                cursor.execute(f'ALTER TABLE "{table}" DROP COLUMN "{column}"')
            return
        cursor.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS {column};")


class Migration(migrations.Migration):

    dependencies = [
        ("homepage", "0039_heroimagem"),
    ]

    operations = [
        migrations.RunPython(drop_hero_imagem_column, migrations.RunPython.noop),
    ]
