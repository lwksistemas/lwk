from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0056_login_lockout_mfa_backup"),
    ]

    operations = [
        migrations.AlterField(
            model_name="nfseemitida",
            name="pdf_url",
            field=models.TextField(blank=True, verbose_name="URL do PDF"),
        ),
    ]
