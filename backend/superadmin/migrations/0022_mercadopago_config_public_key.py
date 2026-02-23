# Migration: Public Key para SDK Mercado Pago no frontend

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0021_loja_provedor_boleto_preferido'),
    ]

    operations = [
        migrations.AddField(
            model_name='mercadopagoconfig',
            name='public_key',
            field=models.CharField(
                blank=True,
                help_text='Chave pública para inicializar MercadoPago.js no frontend',
                max_length=80,
                verbose_name='Public Key (para SDK no frontend)',
            ),
        ),
    ]
