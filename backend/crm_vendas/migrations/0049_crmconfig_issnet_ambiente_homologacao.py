# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0048_remove_produtoservico_crm_ps_unique_codigo_loja_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='crmconfig',
            name='issnet_ambiente_homologacao',
            field=models.BooleanField(
                default=False,
                help_text=(
                    'Se True, o cliente usa o ambiente “homologação” (em RP o WSDL é o mesmo da produção; '
                    'não substitui liberação municipal nem evita E138). Use se a prefeitura orientar.'
                ),
                verbose_name='ISSNet homologação (teste)',
            ),
        ),
    ]
