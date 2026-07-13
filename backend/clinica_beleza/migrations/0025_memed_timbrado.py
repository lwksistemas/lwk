from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0024_professional_nascimento_sexo"),
    ]

    operations = [
        migrations.CreateModel(
            name="MemedTimbrado",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("pdf", models.BinaryField(help_text="Arquivo PDF A4 com papel timbrado da clínica.", verbose_name="PDF timbrado")),
                ("pdf_nome", models.CharField(blank=True, default="", max_length=255, verbose_name="Nome do arquivo")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Timbrado Memed",
                "verbose_name_plural": "Timbrados Memed",
                "db_table": "clinica_beleza_memed_timbrado",
            },
        ),
    ]
