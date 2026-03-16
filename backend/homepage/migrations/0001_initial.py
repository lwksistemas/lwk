# Generated manually for homepage app

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='HeroSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=200)),
                ('subtitulo', models.TextField()),
                ('botao_texto', models.CharField(default='Testar grátis', max_length=100)),
                ('ativo', models.BooleanField(default=True)),
                ('ordem', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Hero Section',
                'verbose_name_plural': 'Hero Sections',
                'db_table': 'homepage_hero_section',
                'ordering': ['ordem', 'id'],
            },
        ),
        migrations.CreateModel(
            name='Funcionalidade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=100)),
                ('descricao', models.TextField()),
                ('icone', models.CharField(help_text='Nome do ícone (ex: Users, BarChart) ou emoji', max_length=50)),
                ('ordem', models.PositiveIntegerField(default=0)),
                ('ativo', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Funcionalidade',
                'verbose_name_plural': 'Funcionalidades',
                'db_table': 'homepage_funcionalidade',
                'ordering': ['ordem', 'id'],
            },
        ),
        migrations.CreateModel(
            name='ModuloSistema',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('descricao', models.TextField()),
                ('slug', models.SlugField(blank=True, help_text='Ex: crm-vendas, clinica-estetica', max_length=50)),
                ('icone', models.CharField(blank=True, max_length=50)),
                ('ordem', models.PositiveIntegerField(default=0)),
                ('ativo', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Módulo do Sistema',
                'verbose_name_plural': 'Módulos do Sistema',
                'db_table': 'homepage_modulo_sistema',
                'ordering': ['ordem', 'id'],
            },
        ),
    ]
