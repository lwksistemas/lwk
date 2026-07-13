# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("asaas_integration", "0006_superadminnfseconfig_prestador_email_regime"),
    ]

    operations = [
        migrations.AddField(
            model_name="superadminnfseconfig",
            name="incentivador_cultural",
            field=models.BooleanField(default=False, help_text="Se a empresa é incentivadora cultural", verbose_name="Incentivador Cultural"),
        ),
    ]
