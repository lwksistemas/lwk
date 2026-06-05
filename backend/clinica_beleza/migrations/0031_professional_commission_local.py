# Generated manually — comissão de consulta por local de atendimento

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_beleza', '0030_localatendimento_consulta_local_atendimento'),
    ]

    operations = [
        migrations.AddField(
            model_name='professionalcommission',
            name='local_atendimento',
            field=models.ForeignKey(
                blank=True,
                help_text='Quando tipo = consulta: regra só para este local. Vazio = regra geral.',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='comissoes',
                to='clinica_beleza.localatendimento',
                verbose_name='Local de atendimento',
            ),
        ),
        migrations.AlterField(
            model_name='professionalcommission',
            name='procedure',
            field=models.ForeignKey(
                blank=True,
                help_text='Obrigatório quando tipo = procedimento. Vazio em consulta.',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='comissoes',
                to='clinica_beleza.procedure',
                verbose_name='Procedimento',
            ),
        ),
    ]
