from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0085_cobrar_taxa_com_procedimento"),
    ]

    operations = [
        migrations.AlterField(
            model_name="clinicabelezanfseconfig",
            name="asaas_api_key",
            field=models.TextField(
                blank=True,
                default="",
                verbose_name="API Key Asaas (loja)",
            ),
        ),
    ]
