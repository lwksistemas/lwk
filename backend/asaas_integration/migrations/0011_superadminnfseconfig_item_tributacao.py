from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("asaas_integration", "0010_asaasconfig_webhook_token"),
    ]

    operations = [
        migrations.AddField(
            model_name="superadminnfseconfig",
            name="item_lista_servico",
            field=models.CharField(
                blank=True,
                default="14.01",
                help_text="Item LC 116 com ponto (ex.: 14.01, 1.05). Deve ser compatível com o CNAE.",
                max_length=10,
                verbose_name="Item lista serviço (LC 116)",
            ),
        ),
        migrations.AddField(
            model_name="superadminnfseconfig",
            name="codigo_tributacao_municipio",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Código de tributação cadastrado na prefeitura para este CNPJ/IM (consulte o portal ISS).",
                max_length=20,
                verbose_name="Código tributação municipal",
            ),
        ),
    ]
