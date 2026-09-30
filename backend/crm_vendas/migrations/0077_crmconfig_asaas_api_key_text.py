from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0076_add_nfse_descricao_template"),
    ]

    operations = [
        migrations.AlterField(
            model_name="crmconfig",
            name="asaas_api_key",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Chave de API v3 da conta Asaas da loja (Integrações). Necessária para emissão via Asaas por loja.",
                verbose_name="API Key Asaas (loja)",
            ),
        ),
    ]
