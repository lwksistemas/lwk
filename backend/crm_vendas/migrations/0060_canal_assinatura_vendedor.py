from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0059_crmconfig_asaas_webhook_token"),
    ]

    operations = [
        migrations.AddField(
            model_name="proposta",
            name="canal_assinatura_vendedor",
            field=models.CharField(
                choices=[("email", "E-mail"), ("whatsapp", "WhatsApp")],
                default="email",
                help_text="Canal para enviar link de assinatura ao vendedor após o cliente assinar",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="contrato",
            name="canal_assinatura_vendedor",
            field=models.CharField(
                choices=[("email", "E-mail"), ("whatsapp", "WhatsApp")],
                default="email",
                help_text="Canal para enviar link de assinatura ao vendedor após o cliente assinar",
                max_length=20,
            ),
        ),
    ]
