# Vencimento das contas a receber a prazo (base da inadimplência).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0081_patient_prazo_pagamento"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="data_vencimento",
            field=models.DateField(
                blank=True,
                null=True,
                help_text="Data limite para pagamento quando a consulta é recebida a prazo.",
                verbose_name="Vencimento (a prazo)",
            ),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(
                fields=["loja_id", "status", "data_vencimento"],
                name="cb_payment_venc_idx",
            ),
        ),
    ]
