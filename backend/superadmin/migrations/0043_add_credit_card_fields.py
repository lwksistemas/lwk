# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0042_add_unique_constraints_atalho'),
    ]

    operations = [
        # Adicionar campo forma_pagamento_preferida em Loja
        migrations.AddField(
            model_name='loja',
            name='forma_pagamento_preferida',
            field=models.CharField(
                choices=[
                    ('boleto', 'Boleto Bancário'),
                    ('pix', 'PIX'),
                    ('cartao_credito', 'Cartão de Crédito')
                ],
                default='boleto',
                help_text='Forma de pagamento escolhida pelo administrador (primeira cobrança sempre boleto/PIX)',
                max_length=20
            ),
        ),
        
        # Adicionar campos de cartão em FinanceiroLoja
        migrations.AddField(
            model_name='financeiroloja',
            name='asaas_creditcard_token',
            field=models.CharField(
                blank=True,
                help_text='Token do cartão tokenizado no Asaas para cobranças recorrentes',
                max_length=100
            ),
        ),
        migrations.AddField(
            model_name='financeiroloja',
            name='cartao_ultimos_digitos',
            field=models.CharField(
                blank=True,
                help_text='Últimos 4 dígitos do cartão (para exibição)',
                max_length=4
            ),
        ),
        migrations.AddField(
            model_name='financeiroloja',
            name='cartao_bandeira',
            field=models.CharField(
                blank=True,
                help_text='Bandeira do cartão (Visa, Mastercard, Elo, etc)',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='financeiroloja',
            name='link_pagamento_cartao',
            field=models.URLField(
                blank=True,
                help_text='Link para página de cadastro do cartão (enviado após primeiro pagamento)'
            ),
        ),
        migrations.AddField(
            model_name='financeiroloja',
            name='cartao_cadastrado',
            field=models.BooleanField(
                default=False,
                help_text='Indica se o cartão já foi cadastrado e tokenizado'
            ),
        ),
        migrations.AddField(
            model_name='financeiroloja',
            name='cartao_cadastrado_em',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Data e hora em que o cartão foi cadastrado'
            ),
        ),
        
        # Adicionar índice para forma_pagamento_preferida
        migrations.AddIndex(
            model_name='loja',
            index=models.Index(
                fields=['forma_pagamento_preferida'],
                name='loja_forma_pag_idx'
            ),
        ),
    ]
