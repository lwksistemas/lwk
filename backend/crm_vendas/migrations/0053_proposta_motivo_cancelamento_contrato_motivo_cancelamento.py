from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0052_add_tipo_to_conta_and_empresa_prestadora'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposta',
            name='motivo_cancelamento',
            field=models.TextField(blank=True, default='', help_text='Motivo do cancelamento da proposta'),
        ),
        migrations.AddField(
            model_name='contrato',
            name='motivo_cancelamento',
            field=models.TextField(blank=True, default='', help_text='Motivo do cancelamento do contrato'),
        ),
    ]
