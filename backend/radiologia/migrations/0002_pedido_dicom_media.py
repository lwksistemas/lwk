from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("radiologia", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="pedidoexame",
            name="dicom_instance_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="pedidoexame",
            name="dicom_media_url",
            field=models.TextField(
                blank=True,
                default="",
                help_text="ZIP DICOM arquivado no media server (pasta dicom/{paciente}/)",
            ),
        ),
        migrations.AddField(
            model_name="pedidoexame",
            name="dicom_synced_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddConstraint(
            model_name="pedidoexame",
            constraint=models.UniqueConstraint(
                condition=models.Q(("study_instance_uid", ""), _negated=True),
                fields=("loja_id", "study_instance_uid"),
                name="rad_ped_loja_study_uniq",
            ),
        ),
    ]
