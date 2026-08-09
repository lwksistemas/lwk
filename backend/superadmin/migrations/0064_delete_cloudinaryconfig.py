from django.db import migrations


def _delete_cloudinary_config_table(apps, schema_editor):
    """Remove a tabela legada apenas se ela realmente existir no banco."""
    if schema_editor.connection.vendor == "sqlite":
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=%s",
                ["superadmin_cloudinary_config"],
            )
            if not cursor.fetchone():
                return
    schema_editor.delete_model(apps.get_model("superadmin", "CloudinaryConfig"))


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0063_loja_telefone_email_contato"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(
                    name="CloudinaryConfig",
                ),
            ],
            database_operations=[
                migrations.RunPython(_delete_cloudinary_config_table, migrations.RunPython.noop),
            ],
        ),
    ]
