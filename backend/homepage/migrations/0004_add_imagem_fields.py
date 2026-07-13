# Generated manually

from django.db import migrations


def _column_exists(cursor, vendor, table, column):
    if vendor == "sqlite":
        cursor.execute(f'PRAGMA table_info("{table}")')
        return any(row[1] == column for row in cursor.fetchall())
    cursor.execute(
        """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
        """,
        [table, column],
    )
    return cursor.fetchone() is not None


def add_imagem_if_not_exists(apps, schema_editor):
    """Adiciona campos imagem apenas se não existirem (PostgreSQL ou SQLite)."""
    from django.db import connection

    targets = (
        ("homepage_funcionalidade", "imagem"),
        ("homepage_hero_section", "imagem"),
        ("homepage_modulo_sistema", "imagem"),
    )

    with connection.cursor() as cursor:
        vendor = connection.vendor
        for table, column in targets:
            if _column_exists(cursor, vendor, table, column):
                continue
            cursor.execute(
                f'ALTER TABLE "{table}" ADD COLUMN "{column}" VARCHAR(500) NULL',
            )


class Migration(migrations.Migration):

    dependencies = [
        ("homepage", "0003_herosection_botao_principal_ativo"),
    ]

    operations = [
        migrations.RunPython(add_imagem_if_not_exists, migrations.RunPython.noop),
    ]
