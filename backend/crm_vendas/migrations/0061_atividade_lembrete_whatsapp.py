from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0060_canal_assinatura_vendedor'),
    ]

    operations = [
        migrations.AddField(
            model_name='atividade',
            name='lembrete_whatsapp',
            field=models.BooleanField(
                default=False,
                help_text='Enviar lembretes automáticos por WhatsApp 24h e 2h antes da atividade',
            ),
        ),
        migrations.AddField(
            model_name='atividade',
            name='lembrete_whatsapp_telefone',
            field=models.CharField(
                blank=True,
                help_text='Número para lembretes automáticos (ex: 5511999999999)',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='atividade',
            name='lembrete_24h_enviado_em',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='atividade',
            name='lembrete_2h_enviado_em',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
