from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("radiologia", "0004_equipamento_vinculo_dicom"),
    ]

    operations = [
        migrations.AddField(
            model_name="equipamento",
            name="liberado_pelo_superadmin",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="equipamento",
            name="maquina_superadmin_id",
            field=models.IntegerField(blank=True, db_index=True, null=True),
        ),
    ]
