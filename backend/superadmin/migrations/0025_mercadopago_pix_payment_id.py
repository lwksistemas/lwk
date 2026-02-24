# Mercado Pago PIX: campo para ID do pagamento PIX (igual Asaas: boleto + PIX)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0024_financeiroloja_mercadopago_payment_id_index'),
    ]

    operations = [
        migrations.AddField(
            model_name='financeiroloja',
            name='mercadopago_pix_payment_id',
            field=models.CharField(blank=True, help_text='ID do pagamento PIX no Mercado Pago', max_length=100),
        ),
        migrations.AddField(
            model_name='pagamentoloja',
            name='mercadopago_pix_payment_id',
            field=models.CharField(blank=True, help_text='ID do pagamento PIX no Mercado Pago', max_length=100),
        ),
    ]
