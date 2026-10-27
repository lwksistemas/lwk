import django.db.models.deletion
from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0093_financeiro_paciente_prazo_e_anterior"),
    ]

    operations = [
        migrations.AddField(
            model_name="procedureprotocol",
            name="desconto_escopo",
            field=models.CharField(
                choices=[("total", "No total"), ("individual", "Em cada procedimento")],
                default="total",
                max_length=20,
                verbose_name="Onde aplica o desconto",
            ),
        ),
        migrations.AddField(
            model_name="procedureprotocol",
            name="desconto_tipo",
            field=models.CharField(
                blank=True,
                default="percentual",
                max_length=20,
                verbose_name="Desconto do total",
            ),
        ),
        migrations.AddField(
            model_name="procedureprotocol",
            name="desconto_valor",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=10,
                verbose_name="Desconto do total",
            ),
        ),
        migrations.CreateModel(
            name="ProtocoloProcedimento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                (
                    "desconto_tipo",
                    models.CharField(blank=True, default="", max_length=20, verbose_name="Desconto deste procedimento"),
                ),
                (
                    "desconto_valor",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        max_digits=10,
                        verbose_name="Desconto informado",
                    ),
                ),
                ("ordem", models.PositiveIntegerField(default=0, verbose_name="Ordem")),
                (
                    "procedure",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="promocoes",
                        to="clinica_beleza.procedure",
                        verbose_name="Procedimento",
                    ),
                ),
                (
                    "protocol",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="itens",
                        to="clinica_beleza.procedureprotocol",
                        verbose_name="Protocolo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Procedimento da promoção",
                "verbose_name_plural": "Procedimentos da promoção",
                "db_table": "clinica_beleza_protocolo_item",
                "ordering": ["ordem", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="protocoloprocedimento",
            constraint=models.UniqueConstraint(
                fields=("protocol", "procedure"),
                name="cb_protocolo_item_uniq",
            ),
        ),
    ]
