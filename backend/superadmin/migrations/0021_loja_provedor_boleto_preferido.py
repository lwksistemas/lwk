# Migration: escolha de provedor de boleto por loja (Asaas ou Mercado Pago)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0020_mercadopago_config_e_provedor_boleto'),
    ]

    operations = [
        migrations.AddField(
            model_name='loja',
            name='provedor_boleto_preferido',
            field=models.CharField(
                choices=[('asaas', 'Asaas'), ('mercadopago', 'Mercado Pago')],
                default='asaas',
                help_text='Provedor de boleto a usar nas cobranças desta loja',
                max_length=20,
            ),
        ),
    ]
