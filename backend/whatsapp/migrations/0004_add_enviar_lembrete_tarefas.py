# Campo para lembretes de tarefas do calendário CRM

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('whatsapp', '0003_whatsapp_por_loja'),
    ]

    operations = [
        migrations.AddField(
            model_name='whatsappconfig',
            name='enviar_lembrete_tarefas',
            field=models.BooleanField(
                default=True,
                help_text='Lembretes de atividades do CRM nas próximas 24h',
                verbose_name='Enviar lembrete de tarefas do calendário (CRM)',
            ),
        ),
    ]
