from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0062_crmconfig_colunas_contas_contatos"),
    ]

    operations = [
        migrations.AddField(
            model_name="assinaturadigital",
            name="link_enviado_em",
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text="Quando o link de assinatura foi enviado ao assinante (e-mail/WhatsApp)",
            ),
        ),
    ]
