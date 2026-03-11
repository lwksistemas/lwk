# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0007_backfill_vendedor_lead_conta'),
    ]

    operations = [
        migrations.AddField(
            model_name='oportunidade',
            name='data_fechamento_ganho',
            field=models.DateField(blank=True, null=True, help_text='Data em que a oportunidade foi fechada como ganha'),
        ),
        migrations.AddField(
            model_name='oportunidade',
            name='data_fechamento_perdido',
            field=models.DateField(blank=True, null=True, help_text='Data em que a oportunidade foi fechada como perdida'),
        ),
        migrations.AddField(
            model_name='oportunidade',
            name='valor_comissao',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, help_text='Valor da comissão para esta oportunidade'),
        ),
        migrations.AddIndex(
            model_name='oportunidade',
            index=models.Index(fields=['loja_id', 'data_fechamento_ganho'], name='crm_opor_loja_dtfechganho_idx'),
        ),
        migrations.AddIndex(
            model_name='oportunidade',
            index=models.Index(fields=['loja_id', 'data_fechamento_perdido'], name='crm_opor_loja_dtfechperd_idx'),
        ),
    ]
