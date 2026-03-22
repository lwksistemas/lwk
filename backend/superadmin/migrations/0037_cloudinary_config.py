# Generated migration for CloudinaryConfig model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0036_fix_financeiro_fk_cascade'),
    ]

    operations = [
        migrations.CreateModel(
            name='CloudinaryConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('singleton_key', models.CharField(default='config', max_length=10, unique=True)),
                ('cloud_name', models.CharField(blank=True, max_length=100, verbose_name='Cloud Name')),
                ('api_key', models.CharField(blank=True, max_length=100, verbose_name='API Key')),
                ('api_secret', models.CharField(blank=True, max_length=100, verbose_name='API Secret')),
                ('enabled', models.BooleanField(default=False, verbose_name='Integração habilitada')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Configuração Cloudinary',
                'verbose_name_plural': 'Configurações Cloudinary',
                'db_table': 'superadmin_cloudinary_config',
            },
        ),
    ]
