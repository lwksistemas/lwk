# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nfse_integration', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='nfse',
            name='asaas_invoice_id',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='Identificador inv_xxxxx retornado pela API (sincroniza situação com o painel Asaas)',
                max_length=40,
                verbose_name='ID da NF no Asaas',
            ),
        ),
        migrations.AddField(
            model_name='nfse',
            name='asaas_payment_id',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='Identificador pay_xxxxx da cobrança vinculada à NFS-e',
                max_length=40,
                verbose_name='ID da cobrança no Asaas',
            ),
        ),
        migrations.AddIndex(
            model_name='nfse',
            index=models.Index(fields=['loja_id', 'asaas_invoice_id'], name='nfse_loja_asaas_inv_idx'),
        ),
    ]
