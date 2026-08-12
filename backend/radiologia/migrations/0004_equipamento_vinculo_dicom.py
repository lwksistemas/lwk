from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("radiologia", "0003_equipamento_serial_codigo"),
    ]

    operations = [
        migrations.AddField(
            model_name="equipamento",
            name="orthanc_study_id_vinculo",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="equipamento",
            name="vinculado_em",
            field=models.DateTimeField(
                blank=True,
                help_text="Quando o exame de vínculo DICOM confirmou o serial do aparelho",
                null=True,
            ),
        ),
    ]
