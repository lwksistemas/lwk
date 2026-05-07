from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0054_proposta_status_pedido'),
    ]

    operations = [
        migrations.AddField(
            model_name='produtoservico',
            name='recorrencia',
            field=models.CharField(
                choices=[
                    ('unico', 'Único (adesão/implantação)'),
                    ('mensal', 'Mensal'),
                    ('trimestral', 'Trimestral'),
                    ('anual', 'Anual'),
                ],
                default='unico',
                help_text='Tipo de cobrança: único (adesão) ou recorrente (mensal, trimestral, anual)',
                max_length=20,
            ),
        ),
    ]
