# Generated manually on 2026-03-18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0022_add_contrato_template'),
    ]

    operations = [
        # Adicionar campos de assinatura em Proposta
        migrations.AddField(
            model_name='proposta',
            name='nome_vendedor_assinatura',
            field=models.CharField(
                max_length=255,
                blank=True,
                help_text='Nome do vendedor para assinatura no PDF'
            ),
        ),
        migrations.AddField(
            model_name='proposta',
            name='nome_cliente_assinatura',
            field=models.CharField(
                max_length=255,
                blank=True,
                help_text='Nome do cliente para assinatura no PDF'
            ),
        ),
        # Adicionar campos de assinatura em Contrato
        migrations.AddField(
            model_name='contrato',
            name='nome_vendedor_assinatura',
            field=models.CharField(
                max_length=255,
                blank=True,
                help_text='Nome do vendedor para assinatura no PDF'
            ),
        ),
        migrations.AddField(
            model_name='contrato',
            name='nome_cliente_assinatura',
            field=models.CharField(
                max_length=255,
                blank=True,
                help_text='Nome do cliente para assinatura no PDF'
            ),
        ),
    ]
