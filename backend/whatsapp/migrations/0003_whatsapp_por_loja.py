# Sincronização WhatsApp por loja: número, token, phone_id, ativo; log com loja

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0001_initial'),
        ('whatsapp', '0002_whatsappconfig'),
    ]

    operations = [
        migrations.AddField(
            model_name='whatsappconfig',
            name='whatsapp_numero',
            field=models.CharField(blank=True, max_length=20, verbose_name='Número WhatsApp (ex: 5511999999999)'),
        ),
        migrations.AddField(
            model_name='whatsappconfig',
            name='whatsapp_phone_id',
            field=models.CharField(blank=True, max_length=64, verbose_name='Phone Number ID (Cloud API)'),
        ),
        migrations.AddField(
            model_name='whatsappconfig',
            name='whatsapp_token',
            field=models.CharField(blank=True, max_length=512, verbose_name='Token de acesso (Cloud API)'),
        ),
        migrations.AddField(
            model_name='whatsappconfig',
            name='whatsapp_ativo',
            field=models.BooleanField(default=False, verbose_name='WhatsApp ativo para esta loja'),
        ),
        migrations.AddField(
            model_name='whatsapplog',
            name='loja',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='whatsapp_logs',
                to='superadmin.loja',
            ),
        ),
    ]
