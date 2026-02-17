# Generated for ETAPA 5 - Motor de regras

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='RegraAutomatica',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('ativa', models.BooleanField(default=True)),
                ('evento', models.CharField(max_length=50)),
                ('acao', models.CharField(help_text='Identificador da ação em código', max_length=50)),
            ],
            options={
                'verbose_name': 'Regra automática',
                'verbose_name_plural': 'Regras automáticas',
                'app_label': 'rules',
            },
        ),
    ]
