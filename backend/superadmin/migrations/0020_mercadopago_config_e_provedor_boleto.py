# Migration: Mercado Pago config e provedor de boleto (Asaas vs Mercado Pago)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0019_remove_profissionalusuario_superadmin_profissionalusuario_user_loja_uniq_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='financeiroloja',
            name='provedor_boleto',
            field=models.CharField(
                choices=[('asaas', 'Asaas'), ('mercadopago', 'Mercado Pago')],
                default='asaas',
                help_text='Provedor usado para gerar boleto desta cobrança',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='financeiroloja',
            name='mercadopago_payment_id',
            field=models.CharField(blank=True, help_text='ID do pagamento no Mercado Pago', max_length=100),
        ),
        migrations.AddField(
            model_name='pagamentoloja',
            name='provedor_boleto',
            field=models.CharField(
                choices=[('asaas', 'Asaas'), ('mercadopago', 'Mercado Pago')],
                default='asaas',
                help_text='Provedor do boleto (Asaas ou Mercado Pago)',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='pagamentoloja',
            name='mercadopago_payment_id',
            field=models.CharField(blank=True, help_text='ID do pagamento no Mercado Pago', max_length=100),
        ),
        migrations.CreateModel(
            name='MercadoPagoConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('singleton_key', models.CharField(default='config', max_length=10, unique=True)),
                ('access_token', models.TextField(blank=True, verbose_name='Access Token (Produção ou Teste)')),
                ('enabled', models.BooleanField(default=False, verbose_name='Integração habilitada')),
                ('use_for_boletos', models.BooleanField(
                    default=False,
                    help_text='Se ativo, novas cobranças de lojas usarão boleto via Mercado Pago em vez do Asaas',
                    verbose_name='Usar Mercado Pago para novos boletos',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Configuração Mercado Pago',
                'verbose_name_plural': 'Configurações Mercado Pago',
                'db_table': 'superadmin_mercadopago_config',
            },
        ),
    ]
