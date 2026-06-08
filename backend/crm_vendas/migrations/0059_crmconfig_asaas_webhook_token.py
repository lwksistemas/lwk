from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0058_relatoriocomissao'),
    ]

    operations = [
        migrations.AddField(
            model_name='crmconfig',
            name='asaas_webhook_token',
            field=models.TextField(
                blank=True,
                default='',
                help_text='Token de autenticação do webhook Asaas desta loja (header asaas-access-token).',
                verbose_name='Token webhook Asaas (loja)',
            ),
        ),
    ]
