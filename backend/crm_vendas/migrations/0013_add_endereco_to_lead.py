# Generated manually - add endereço fields to Lead
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0012_remove_origem_choices_constraint'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='cep',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='lead',
            name='logradouro',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='lead',
            name='numero',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='lead',
            name='complemento',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='lead',
            name='bairro',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='lead',
            name='cidade',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='lead',
            name='uf',
            field=models.CharField(blank=True, max_length=2),
        ),
    ]
