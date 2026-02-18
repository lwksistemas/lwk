# Detalhes do suporte: erros de frontend por loja (sessão única)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('suporte', '0003_add_detalhes_tecnicos'),
    ]

    operations = [
        migrations.CreateModel(
            name='ErroFrontend',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_slug', models.CharField(db_index=True, max_length=100)),
                ('mensagem', models.CharField(max_length=500)),
                ('stack', models.TextField(blank=True, default='')),
                ('url', models.CharField(blank=True, default='', max_length=500)),
                ('user_agent', models.CharField(blank=True, default='', max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
                'verbose_name': 'Erro frontend',
                'verbose_name_plural': 'Erros frontend',
            },
        ),
    ]
