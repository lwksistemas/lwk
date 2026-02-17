# ETAPA 4 - Opt-out WhatsApp por paciente (LGPD)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_beleza', '0005_add_appointment_version_updated_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='allow_whatsapp',
            field=models.BooleanField(
                default=True,
                help_text='Se desmarcado, o paciente não recebe mensagens por WhatsApp (LGPD).',
                verbose_name='Permitir WhatsApp',
            ),
        ),
    ]
