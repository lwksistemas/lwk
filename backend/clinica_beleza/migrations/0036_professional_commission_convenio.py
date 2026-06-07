# Generated manually — comissão por procedimento e convênio

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_beleza', '0035_despesa_categoria'),
    ]

    operations = [
        migrations.AddField(
            model_name='professionalcommission',
            name='convenio',
            field=models.ForeignKey(
                blank=True,
                help_text='Opcional em procedimento: regra específica por convênio. Vazio = regra geral.',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='comissoes_profissionais',
                to='clinica_beleza.convenio',
                verbose_name='Convênio',
            ),
        ),
    ]
