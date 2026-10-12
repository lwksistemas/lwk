from django.db import migrations, models


def cifrar_senhas_issnet(apps, schema_editor):
    del schema_editor
    from core.encryption import cifrar_senhas_issnet_no_objeto

    config_model = apps.get_model("crm_vendas", "CRMConfig")
    for config in config_model.objects.all():
        if cifrar_senhas_issnet_no_objeto(config):
            config.save(update_fields=["issnet_senha", "issnet_senha_certificado"])


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0077_crmconfig_asaas_api_key_text"),
    ]

    operations = [
        migrations.AlterField(
            model_name="crmconfig",
            name="issnet_senha",
            field=models.CharField(
                blank=True,
                help_text="Senha de acesso ao webservice ISSNet",
                max_length=500,
                verbose_name="Senha ISSNet",
            ),
        ),
        migrations.AlterField(
            model_name="crmconfig",
            name="issnet_senha_certificado",
            field=models.CharField(
                blank=True,
                help_text="Senha do arquivo .pfx do certificado digital",
                max_length=500,
                verbose_name="Senha do Certificado",
            ),
        ),
        migrations.RunPython(cifrar_senhas_issnet, migrations.RunPython.noop),
    ]
