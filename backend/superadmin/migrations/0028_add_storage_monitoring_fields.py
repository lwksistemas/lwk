# Generated manually for v738

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0027_financeiroloja_data_envio_senha_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='loja',
            name='storage_usado_mb',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Espaço em disco usado pela loja (em MB)', max_digits=10),
        ),
        migrations.AddField(
            model_name='loja',
            name='storage_limite_mb',
            field=models.IntegerField(default=500, help_text='Limite de storage da loja (em MB) - baseado no plano'),
        ),
        migrations.AddField(
            model_name='loja',
            name='storage_alerta_enviado',
            field=models.BooleanField(default=False, help_text='Indica se alerta de 80% já foi enviado'),
        ),
        migrations.AddField(
            model_name='loja',
            name='storage_ultima_verificacao',
            field=models.DateTimeField(blank=True, help_text='Data da última verificação de storage', null=True),
        ),
        migrations.AddIndex(
            model_name='loja',
            index=models.Index(fields=['storage_ultima_verificacao'], name='loja_storage_check_idx'),
        ),
    ]
