from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0064_delete_cloudinaryconfig"),
    ]

    operations = [
        migrations.AddField(
            model_name="planoassinatura",
            name="tem_fotos_paciente",
            field=models.BooleanField(
                default=False,
                help_text="Permite upload de fotos do paciente (servidor de mídia).",
            ),
        ),
        migrations.AddField(
            model_name="planoassinatura",
            name="tem_memed",
            field=models.BooleanField(
                default=False,
                help_text="Permite prescrição digital Memed.",
            ),
        ),
    ]
