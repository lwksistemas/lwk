# Generated manually to remove origem choices constraint
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0009_crmconfig'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lead',
            name='origem',
            field=models.CharField(
                max_length=50,
                default='site',
                help_text='Origem do lead (valores configuráveis via CRMConfig)'
            ),
        ),
    ]
