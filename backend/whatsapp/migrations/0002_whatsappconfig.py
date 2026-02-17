# ETAPA 4 - Configuração WhatsApp por loja

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0001_initial'),
        ('whatsapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='WhatsAppConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enviar_confirmacao', models.BooleanField(default=True, verbose_name='Enviar confirmação de agendamento')),
                ('enviar_lembrete_24h', models.BooleanField(default=True, verbose_name='Enviar lembrete 24h antes')),
                ('enviar_lembrete_2h', models.BooleanField(default=True, verbose_name='Enviar lembrete 2h antes')),
                ('enviar_cobranca', models.BooleanField(default=True, verbose_name='Enviar cobrança financeiro')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('loja', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='whatsapp_config', to='superadmin.loja')),
            ],
            options={
                'verbose_name': 'Configuração WhatsApp',
                'verbose_name_plural': 'Configurações WhatsApp',
                'app_label': 'whatsapp',
            },
        ),
    ]
