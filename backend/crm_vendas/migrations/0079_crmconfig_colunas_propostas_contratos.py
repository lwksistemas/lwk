from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0078_cifrar_senhas_issnet"),
    ]

    operations = [
        migrations.AddField(
            model_name="crmconfig",
            name="colunas_propostas",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Colunas visíveis na listagem de propostas",
            ),
        ),
        migrations.AddField(
            model_name="crmconfig",
            name="colunas_contratos",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Colunas visíveis na listagem de contratos",
            ),
        ),
    ]
