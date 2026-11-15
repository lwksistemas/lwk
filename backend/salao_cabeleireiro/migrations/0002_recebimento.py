from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("salao_cabeleireiro", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Recebimento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("valor_servico", models.DecimalField(decimal_places=2, max_digits=10)),
                ("desconto", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=10)),
                ("valor", models.DecimalField(decimal_places=2, max_digits=10)),
                ("forma", models.CharField(choices=[("dinheiro", "Dinheiro"), ("pix", "Pix"), ("debito", "Débito"), ("credito", "Crédito")], max_length=20)),
                ("comissao_percentual", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=5)),
                ("comissao_valor", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=10)),
                ("observacao", models.CharField(blank=True, default="", max_length=200)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("agendamento", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="recebimentos", to="salao_cabeleireiro.agendamento")),
                ("profissional", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="recebimentos", to="salao_cabeleireiro.profissional")),
            ],
            options={
                "verbose_name": "Recebimento",
                "ordering": ["-created_at"],
                "constraints": [
                    models.UniqueConstraint(
                        condition=models.Q(is_active=True),
                        fields=("agendamento",),
                        name="salao_um_recebimento_ativo",
                    )
                ],
            },
        ),
    ]
