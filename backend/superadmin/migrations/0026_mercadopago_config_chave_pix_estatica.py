# Generated migration: chave PIX estática para fallback na página do boleto

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0025_mercadopago_pix_payment_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='mercadopagoconfig',
            name='chave_pix_estatica',
            field=models.CharField(
                blank=True,
                help_text='Chave PIX (copia e cola) exibida na página do boleto quando não houver PIX dinâmico do Mercado Pago.',
                max_length=120,
                verbose_name='Chave PIX estática (fallback)',
            ),
        ),
    ]
