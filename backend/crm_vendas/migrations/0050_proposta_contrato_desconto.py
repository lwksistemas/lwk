"""
Adiciona campos de desconto em Proposta e Contrato.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0049_crmconfig_issnet_ambiente_homologacao'),
    ]

    operations = [
        # Proposta
        migrations.AddField(
            model_name='proposta',
            name='desconto_tipo',
            field=models.CharField(
                max_length=15,
                choices=[('percentual', 'Percentual'), ('valor', 'Valor fixo')],
                default='percentual',
                help_text='Tipo de desconto: percentual (%) ou valor fixo (R$)',
            ),
        ),
        migrations.AddField(
            model_name='proposta',
            name='desconto_valor',
            field=models.DecimalField(
                max_digits=12,
                decimal_places=2,
                default=0,
                help_text='Valor do desconto (percentual ou fixo, conforme desconto_tipo)',
            ),
        ),
        # Contrato
        migrations.AddField(
            model_name='contrato',
            name='desconto_tipo',
            field=models.CharField(
                max_length=15,
                choices=[('percentual', 'Percentual'), ('valor', 'Valor fixo')],
                default='percentual',
                help_text='Tipo de desconto: percentual (%) ou valor fixo (R$)',
            ),
        ),
        migrations.AddField(
            model_name='contrato',
            name='desconto_valor',
            field=models.DecimalField(
                max_digits=12,
                decimal_places=2,
                default=0,
                help_text='Valor do desconto (percentual ou fixo, conforme desconto_tipo)',
            ),
        ),
    ]
