from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0094_protocolo_promocao"),
    ]

    operations = [
        migrations.AddField(
            model_name="protocolocontrato",
            name="desconto_escopo",
            field=models.CharField(
                choices=[("total", "No total"), ("individual", "Em cada procedimento")],
                default="total",
                max_length=20,
                verbose_name="Onde aplica o desconto",
            ),
        ),
        migrations.AddField(
            model_name="protocolocontratoprocedimento",
            name="desconto_tipo",
            field=models.CharField(
                blank=True,
                default="",
                max_length=20,
                verbose_name="Desconto deste procedimento",
            ),
        ),
        migrations.AddField(
            model_name="protocolocontratoprocedimento",
            name="desconto_valor",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=10,
                verbose_name="Desconto informado",
            ),
        ),
    ]
