from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asaas_integration', '0009_superadminnfseconfig_nacional_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='asaasconfig',
            name='webhook_token',
            field=models.TextField(
                blank=True,
                default='',
                verbose_name='Token de autenticação do webhook',
            ),
        ),
    ]
