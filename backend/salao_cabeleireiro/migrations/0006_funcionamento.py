from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("salao_cabeleireiro", "0005_fiscal_config"),
    ]

    operations = [
        migrations.AddField(
            model_name="salaoconfig",
            name="modelo",
            field=models.CharField(default="recepcionista", max_length=20),
        ),
        migrations.AddField(
            model_name="salaoconfig",
            name="local_recebimento",
            field=models.CharField(default="caixa", max_length=20),
        ),
    ]
