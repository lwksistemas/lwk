from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0070_appointment_confirmacao_generation"),
    ]

    operations = [
        migrations.AddField(
            model_name="professional",
            name="foto_url",
            field=models.URLField(
                blank=True,
                default="",
                help_text="Foto de perfil do profissional (servidor de mídia).",
                max_length=500,
                verbose_name="Foto",
            ),
        ),
    ]
