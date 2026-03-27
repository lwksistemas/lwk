# Generated manually for HeroImagem model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homepage', '0038_whyusbenefit'),
    ]

    operations = [
        migrations.CreateModel(
            name='HeroImagem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('imagem', models.URLField(help_text='URL da imagem de fundo do hero', max_length=500)),
                ('titulo', models.CharField(blank=True, help_text='Título opcional para esta imagem', max_length=200)),
                ('ordem', models.PositiveIntegerField(default=0)),
                ('ativo', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Imagem do Hero',
                'verbose_name_plural': 'Imagens do Hero',
                'db_table': 'homepage_hero_imagem',
                'ordering': ['ordem', 'id'],
            },
        ),
    ]
