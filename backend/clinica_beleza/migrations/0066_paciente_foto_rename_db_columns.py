from django.db import migrations, models


FORWARD_SQL = """
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND table_name = 'clinica_beleza_paciente_fotos'
      AND column_name = 'cloudinary_url'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND table_name = 'clinica_beleza_paciente_fotos'
      AND column_name = 'url'
  ) THEN
    ALTER TABLE clinica_beleza_paciente_fotos RENAME COLUMN cloudinary_url TO url;
  END IF;

  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND table_name = 'clinica_beleza_paciente_fotos'
      AND column_name = 'cloudinary_public_id'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND table_name = 'clinica_beleza_paciente_fotos'
      AND column_name = 'public_id'
  ) THEN
    ALTER TABLE clinica_beleza_paciente_fotos
      RENAME COLUMN cloudinary_public_id TO public_id;
  END IF;
END $$;
"""

REVERSE_SQL = """
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND table_name = 'clinica_beleza_paciente_fotos'
      AND column_name = 'url'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND table_name = 'clinica_beleza_paciente_fotos'
      AND column_name = 'cloudinary_url'
  ) THEN
    ALTER TABLE clinica_beleza_paciente_fotos RENAME COLUMN url TO cloudinary_url;
  END IF;

  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND table_name = 'clinica_beleza_paciente_fotos'
      AND column_name = 'public_id'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND table_name = 'clinica_beleza_paciente_fotos'
      AND column_name = 'cloudinary_public_id'
  ) THEN
    ALTER TABLE clinica_beleza_paciente_fotos
      RENAME COLUMN public_id TO cloudinary_public_id;
  END IF;
END $$;
"""


class Migration(migrations.Migration):
    """Renomeia colunas físicas cloudinary_* → url / public_id."""

    dependencies = [
        ("clinica_beleza", "0065_paciente_foto_url_fields_state"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(FORWARD_SQL, REVERSE_SQL),
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
