# Índice para consultas por mercadopago_payment_id (webhook e sync)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0023_alter_financeiroloja_boleto_url'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='financeiroloja',
            index=models.Index(fields=['mercadopago_payment_id'], name='fin_mp_payment_idx'),
        ),
        migrations.AddIndex(
            model_name='pagamentoloja',
            index=models.Index(fields=['mercadopago_payment_id'], name='pag_mp_payment_idx'),
        ),
    ]
