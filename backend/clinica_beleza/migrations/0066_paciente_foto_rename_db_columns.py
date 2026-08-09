from django.db import migrations, models


def _rename_columns(apps, schema_editor, old_to_new: dict[str, str]):
    """Renomeia colunas físicas de forma idempotente, compatível com SQLite e PostgreSQL."""
    if schema_editor.connection.vendor == "postgresql":
        table_name = schema_editor.connection.ops.quote_name("clinica_beleza_paciente_fotos")
        for old_name, new_name in old_to_new.items():
            old_q = schema_editor.connection.ops.quote_name(old_name)
            new_q = schema_editor.connection.ops.quote_name(new_name)
            schema_editor.execute(
                f"""
                DO $$
                BEGIN
                  IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = current_schema()
                      AND table_name = 'clinica_beleza_paciente_fotos'
                      AND column_name = %s
                  ) AND NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = current_schema()
                      AND table_name = 'clinica_beleza_paciente_fotos'
                      AND column_name = %s
                  ) THEN
                    ALTER TABLE {table_name} RENAME COLUMN {old_q} TO {new_q};
                  END IF;
                END $$;
                """,
                [old_name, new_name],
            )
    elif schema_editor.connection.vendor == "sqlite":
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(
                "SELECT name FROM pragma_table_info('clinica_beleza_paciente_fotos')"
            )
            columns = {row[0] for row in cursor.fetchall()}
            for old_name, new_name in old_to_new.items():
                if old_name in columns and new_name not in columns:
                    schema_editor.execute(
                        f"ALTER TABLE clinica_beleza_paciente_fotos RENAME COLUMN {old_name} TO {new_name};"
                    )


def _forward(apps, schema_editor):
    _rename_columns(apps, schema_editor, {"cloudinary_url": "url", "cloudinary_public_id": "public_id"})


def _reverse(apps, schema_editor):
    _rename_columns(apps, schema_editor, {"url": "cloudinary_url", "public_id": "cloudinary_public_id"})


class Migration(migrations.Migration):
    """Renomeia colunas físicas cloudinary_* → url / public_id."""

    dependencies = [
        ("clinica_beleza", "0065_paciente_foto_url_fields_state"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(_forward, _reverse),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="pacientefotoacompanhamento",
                    name="url",
                    field=models.URLField(max_length=500),
                ),
                migrations.AlterField(
                    model_name="pacientefotoacompanhamento",
                    name="public_id",
                    field=models.CharField(blank=True, default="", max_length=255),
                ),
            ],
        ),
    ]
