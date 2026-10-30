from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0074_financeiroloja_degustacao_apos_pagamento"),
    ]

    operations = [
        migrations.DeleteModel(name="MaquinaRadiologia"),
        migrations.DeleteModel(name="ContratoPacsLoja"),
    ]
