from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0061_atividade_lembrete_whatsapp'),
    ]

    operations = [
        migrations.AddField(
            model_name='crmconfig',
            name='colunas_contas',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Colunas visíveis na listagem de contas',
            ),
        ),
        migrations.AddField(
            model_name='crmconfig',
            name='colunas_contatos',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Colunas visíveis na listagem de contatos',
            ),
        ),
    ]
