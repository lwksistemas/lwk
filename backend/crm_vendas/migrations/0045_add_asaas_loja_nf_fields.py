# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0044_add_nfse_config'),
    ]

    operations = [
        migrations.AddField(
            model_name='crmconfig',
            name='asaas_api_key',
            field=models.CharField(
                blank=True,
                help_text='Chave de API v3 da conta Asaas da loja (Integrações). Necessária para emissão via Asaas por loja.',
                max_length=255,
                verbose_name='API Key Asaas (loja)',
            ),
        ),
        migrations.AddField(
            model_name='crmconfig',
            name='asaas_sandbox',
            field=models.BooleanField(
                default=False,
                help_text='Se True, usa api sandbox.asaas.com (chave de testes).',
                verbose_name='Asaas sandbox (homologação)',
            ),
        ),
    ]
