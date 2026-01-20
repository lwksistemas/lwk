# Generated migration for sync and block fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0008_financeiroloja_asaas_customer_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='loja',
            name='is_blocked',
            field=models.BooleanField(default=False, help_text='Loja bloqueada por inadimplência'),
        ),
        migrations.AddField(
            model_name='loja',
            name='blocked_at',
            field=models.DateTimeField(blank=True, help_text='Data do bloqueio', null=True),
        ),
        migrations.AddField(
            model_name='loja',
            name='blocked_reason',
            field=models.CharField(blank=True, help_text='Motivo do bloqueio', max_length=255),
        ),
        migrations.AddField(
            model_name='loja',
            name='days_overdue',
            field=models.IntegerField(default=0, help_text='Dias em atraso'),
        ),
        migrations.AddField(
            model_name='financeiroloja',
            name='last_sync_at',
            field=models.DateTimeField(blank=True, help_text='Última sincronização com Asaas', null=True),
        ),
        migrations.AddField(
            model_name='financeiroloja',
            name='sync_error',
            field=models.TextField(blank=True, help_text='Último erro de sincronização'),
        ),
    ]