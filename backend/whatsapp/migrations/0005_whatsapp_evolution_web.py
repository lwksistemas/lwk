# WhatsApp Web via Evolution API (provider alternativo à Meta)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("whatsapp", "0004_add_enviar_lembrete_tarefas"),
    ]

    operations = [
        migrations.AddField(
            model_name="whatsappconfig",
            name="whatsapp_provider",
            field=models.CharField(
                choices=[("meta", "Meta Cloud API"), ("evolution", "WhatsApp Web (Evolution)")],
                default="meta",
                max_length=20,
                verbose_name="Provedor WhatsApp",
            ),
        ),
        migrations.AddField(
            model_name="whatsappconfig",
            name="evolution_instance_name",
            field=models.CharField(blank=True, max_length=64, verbose_name="Instância Evolution"),
        ),
        migrations.AddField(
            model_name="whatsappconfig",
            name="whatsapp_connection_status",
            field=models.CharField(
                choices=[
                    ("disconnected", "Desconectado"),
                    ("qr_pending", "Aguardando QR"),
                    ("connected", "Conectado"),
                    ("error", "Erro"),
                ],
                default="disconnected",
                max_length=20,
                verbose_name="Status da conexão (WhatsApp Web)",
            ),
        ),
        migrations.AddField(
            model_name="whatsappconfig",
            name="whatsapp_connected_phone",
            field=models.CharField(blank=True, max_length=32, verbose_name="Número conectado (WhatsApp Web)"),
        ),
        migrations.AddField(
            model_name="whatsappconfig",
            name="whatsapp_connected_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Conectado em (WhatsApp Web)"),
        ),
    ]
