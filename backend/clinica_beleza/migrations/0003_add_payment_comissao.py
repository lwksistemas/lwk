# Migration: Comissão no Payment (Financeiro da Clínica)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_beleza', '0002_bloqueio_horario'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='comissao_percentual',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Comissão %'),
        ),
        migrations.AddField(
            model_name='payment',
            name='comissao_valor',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Comissão R$'),
        ),
    ]
