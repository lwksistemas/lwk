# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0025_remove_genericforeignkey_assinatura'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposta',
            name='numero',
            field=models.CharField(blank=True, help_text='Número sequencial da proposta (ex: 001, 002, 003)', max_length=50),
        ),
    ]
