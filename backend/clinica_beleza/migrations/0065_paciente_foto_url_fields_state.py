from django.db import migrations, models


class Migration(migrations.Migration):
    """Renomeia campos no estado Django; colunas físicas permanecem cloudinary_*."""

    dependencies = [
        ("clinica_beleza", "0064_nfse_emitir_auto_default_false"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name="pacientefotoacompanhamento",
                    name="cloudinary_url",
                ),
                migrations.RemoveField(
                    model_name="pacientefotoacompanhamento",
                    name="cloudinary_public_id",
                ),
                migrations.AddField(
                    model_name="pacientefotoacompanhamento",
                    name="url",
                    field=models.URLField(db_column="cloudinary_url", max_length=500),
                ),
                migrations.AddField(
                    model_name="pacientefotoacompanhamento",
                    name="public_id",
                    field=models.CharField(
                        blank=True,
                        db_column="cloudinary_public_id",
                        default="",
                        max_length=255,
                    ),
                ),
            ],
            database_operations=[],
        ),
    ]
