# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0019_alter_crmconfig_loja_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='crmconfig',
            name='proposta_conteudo_padrao',
            field=models.TextField(
                blank=True,
                default='',
                help_text='Conteúdo padrão da proposta comercial (reutilizado ao criar novas propostas)'
            ),
        ),
    ]
