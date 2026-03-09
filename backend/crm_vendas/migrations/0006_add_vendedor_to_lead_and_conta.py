# Generated manually - vendedor em Lead e Conta para cadastros do vendedor aparecerem
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0005_add_duracao_minutos'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='vendedor',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='leads',
                to='crm_vendas.vendedor',
                help_text='Vendedor responsável pelo lead (quando criado por vendedor)',
            ),
        ),
        migrations.AddField(
            model_name='conta',
            name='vendedor',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='contas',
                to='crm_vendas.vendedor',
                help_text='Vendedor responsável pela conta (quando criado por vendedor)',
            ),
        ),
    ]
