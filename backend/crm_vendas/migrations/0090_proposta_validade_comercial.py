from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0089_crmconfig_logo_assinatura"),
    ]

    operations = [
        migrations.AddField(
            model_name="proposta",
            name="validade_dias",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Prazo comercial em dias. Não muda o prazo do link nem os valores.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="proposta",
            name="validade_inicio",
            field=models.DateField(
                blank=True,
                help_text="Início da validade comercial. Vazio usa a data de envio ou de criação.",
                null=True,
            ),
        ),
    ]
