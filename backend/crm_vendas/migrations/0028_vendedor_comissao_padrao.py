# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0027_add_complete_company_data_to_conta'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendedor',
            name='comissao_padrao',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Porcentagem de comissão padrão (ex: 5.00 para 5%)', max_digits=5),
        ),
    ]
