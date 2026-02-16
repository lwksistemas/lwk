# Generated manually for notificacoes app

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=120)),
                ('mensagem', models.TextField()),
                ('tipo', models.CharField(choices=[('agendamento', 'Agendamento'), ('cancelamento', 'Cancelamento'), ('lembrete', 'Lembrete'), ('financeiro', 'Financeiro'), ('sistema', 'Sistema')], max_length=30)),
                ('canal', models.CharField(choices=[('in_app', 'In App'), ('push', 'Push'), ('whatsapp', 'WhatsApp'), ('email', 'Email')], default='in_app', max_length=20)),
                ('status', models.CharField(choices=[('pendente', 'Pendente'), ('enviado', 'Enviado'), ('falhou', 'Falhou'), ('lido', 'Lido')], default='pendente', max_length=20)),
                ('metadata', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Notificação',
                'verbose_name_plural': 'Notificações',
                'ordering': ['-created_at'],
            },
        ),
    ]
