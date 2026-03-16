# Generated manually - allow blank icone for Funcionalidade

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homepage', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='funcionalidade',
            name='icone',
            field=models.CharField(blank=True, default='', help_text='Nome do ícone (ex: Users, BarChart) ou emoji', max_length=50),
        ),
    ]
