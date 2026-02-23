# Alteração do help_text de boleto_url (Asaas ou Mercado Pago)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0022_mercadopago_config_public_key'),
    ]

    operations = [
        migrations.AlterField(
            model_name='financeiroloja',
            name='boleto_url',
            field=models.URLField(
                blank=True,
                help_text='URL do boleto (Asaas ou Mercado Pago)',
            ),
        ),
    ]
