# Generated manually - ETAPA 4 WhatsApp

from django.conf import settings
from django.db import migrations, models
from django.db.models.deletion import SET_NULL


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WhatsAppLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telefone', models.CharField(max_length=20)),
                ('mensagem', models.TextField()),
                ('status', models.CharField(choices=[('enviado', 'Enviado'), ('falhou', 'Falhou')], max_length=20)),
                ('response', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=SET_NULL, related_name='whatsapp_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Log WhatsApp',
                'verbose_name_plural': 'Logs WhatsApp',
                'ordering': ['-created_at'],
                'app_label': 'whatsapp',
            },
        ),
    ]
