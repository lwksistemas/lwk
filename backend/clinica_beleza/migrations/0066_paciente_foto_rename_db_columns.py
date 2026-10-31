from django.db import migrations, models


def _forward(apps, schema_editor):
    return None


def _reverse(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    """Ajusta o estado do modelo. As colunas físicas já são url e public_id."""

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
