from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_beleza', '0047_retorno_gratuito_agenda'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='foto_url',
            field=models.URLField(
                blank=True,
                default='',
                help_text='Foto de perfil do cliente (Cloudinary).',
                max_length=500,
                verbose_name='Foto',
            ),
        ),
    ]
