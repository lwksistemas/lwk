# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0038_historicobackup_configuracaobackup_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoginConfigSistema',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('superadmin', 'Superadmin'), ('suporte', 'Suporte')], help_text='Tipo de login (superadmin ou suporte)', max_length=20, unique=True)),
                ('logo', models.URLField(blank=True, help_text='URL da logo exibida na tela de login', max_length=500)),
                ('login_background', models.URLField(blank=True, help_text='URL da imagem de fundo da tela de login', max_length=500)),
                ('cor_primaria', models.CharField(default='#10B981', help_text='Cor primária em hexadecimal (ex: #10B981)', max_length=7)),
                ('cor_secundaria', models.CharField(default='#059669', help_text='Cor secundária em hexadecimal (ex: #059669)', max_length=7)),
                ('titulo', models.CharField(blank=True, help_text='Título exibido na tela de login', max_length=100)),
                ('subtitulo', models.CharField(blank=True, help_text='Subtítulo exibido na tela de login', max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Configuração de Login do Sistema',
                'verbose_name_plural': 'Configurações de Login do Sistema',
                'db_table': 'superadmin_login_config_sistema',
            },
        ),
    ]
