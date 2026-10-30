from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0073_financeiroloja_degustacao"),
    ]

    operations = [
        migrations.AddField(
            model_name="financeiroloja",
            name="degustacao_dias_apos_pagamento",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="Dias de demonstração que começam quando o boleto em aberto for pago.",
                null=True,
            ),
        ),
    ]
