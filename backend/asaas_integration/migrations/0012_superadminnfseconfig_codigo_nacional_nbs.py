from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("asaas_integration", "0011_superadminnfseconfig_item_tributacao"),
    ]

    operations = [
        migrations.AddField(
            model_name="superadminnfseconfig",
            name="codigo_tributacao_nacional",
            field=models.CharField(
                blank=True,
                default="",
                help_text="cTribNac de 6 dígitos. Ex.: 01.07.01.",
                max_length=20,
                verbose_name="Código de tributação nacional",
            ),
        ),
        migrations.AddField(
            model_name="superadminnfseconfig",
            name="codigo_nbs",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Nomenclatura Brasileira de Serviços. Ex.: 1.1508.00.00.",
                max_length=20,
                verbose_name="Código da NBS",
            ),
        ),
    ]
