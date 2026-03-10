# Generated manually to add comissao_percentual field

from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_estetica', '0013_bloqueioagenda_bloqueio_periodo_idx'),
    ]

    operations = [
        migrations.AddField(
            model_name='profissional',
            name='comissao_percentual',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                max_digits=5,
                verbose_name='Comissão %'
            ),
        ),
    ]
