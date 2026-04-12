# Generated manually
"""
Muda issnet_certificado de FileField para BinaryField (Heroku disco efêmero).
Adiciona issnet_certificado_nome para guardar o nome original do arquivo.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0046_add_portal_emissor_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='crmconfig',
            name='issnet_certificado',
        ),
        migrations.AddField(
            model_name='crmconfig',
            name='issnet_certificado',
            field=models.BinaryField(blank=True, null=True, verbose_name='Certificado Digital A1',
                                     help_text='Conteúdo binário do arquivo .pfx (salvo no banco)'),
        ),
        migrations.AddField(
            model_name='crmconfig',
            name='issnet_certificado_nome',
            field=models.CharField(blank=True, max_length=255, verbose_name='Nome do arquivo .pfx'),
        ),
    ]
