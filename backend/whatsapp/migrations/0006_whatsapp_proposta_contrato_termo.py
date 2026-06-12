from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('whatsapp', '0005_whatsapp_evolution_web'),
    ]

    operations = [
        migrations.AddField(
            model_name='whatsappconfig',
            name='enviar_proposta_whatsapp',
            field=models.BooleanField(
                default=True,
                verbose_name='Permitir envio de proposta por WhatsApp (CRM)',
            ),
        ),
        migrations.AddField(
            model_name='whatsappconfig',
            name='enviar_contrato_whatsapp',
            field=models.BooleanField(
                default=True,
                verbose_name='Permitir envio de contrato por WhatsApp (CRM)',
            ),
        ),
        migrations.AddField(
            model_name='whatsappconfig',
            name='enviar_termo_consentimento_whatsapp',
            field=models.BooleanField(
                default=True,
                verbose_name='Permitir envio de termo de consentimento por WhatsApp',
            ),
        ),
    ]
