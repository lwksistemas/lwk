"""
Expande campos de senha/credenciais para suportar valores criptografados (Fernet).
Tokens Fernet são ~2x o tamanho do plaintext + overhead base64.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asaas_integration', '0007_superadminnfseconfig_incentivador_cultural'),
    ]

    operations = [
        migrations.AlterField(
            model_name='superadminnfseconfig',
            name='issnet_usuario',
            field=models.CharField(blank=True, max_length=500, verbose_name='Usuário ISSNet'),
        ),
        migrations.AlterField(
            model_name='superadminnfseconfig',
            name='issnet_senha',
            field=models.CharField(blank=True, max_length=500, verbose_name='Senha ISSNet'),
        ),
        migrations.AlterField(
            model_name='superadminnfseconfig',
            name='issnet_senha_certificado',
            field=models.CharField(blank=True, max_length=500, verbose_name='Senha do Certificado'),
        ),
    ]
