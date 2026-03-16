# Add cpf_cnpj to Lead

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0015_add_produto_servico_proposta_contrato'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='cpf_cnpj',
            field=models.CharField(blank=True, help_text='CPF ou CNPJ do lead', max_length=18),
        ),
    ]
