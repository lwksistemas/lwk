from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("salao_cabeleireiro", "0009_produto_fornecedor"),
    ]

    operations = [
        migrations.AddField(
            model_name="profissional",
            name="comissao_tipo",
            field=models.CharField(default="percentual", max_length=12),
        ),
        migrations.AddField(
            model_name="profissional",
            name="comissao_fixa",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=10),
        ),
        migrations.CreateModel(
            name="ComissaoProcedimento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(default="percentual", max_length=12)),
                ("valor", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=10)),
                (
                    "profissional",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comissoes",
                        to="salao_cabeleireiro.profissional",
                    ),
                ),
                (
                    "servico",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comissoes",
                        to="salao_cabeleireiro.servico",
                    ),
                ),
            ],
            options={"verbose_name": "Comissão do procedimento"},
        ),
        migrations.AddConstraint(
            model_name="comissaoprocedimento",
            constraint=models.UniqueConstraint(fields=("profissional", "servico"), name="salao_comissao_profissional_servico"),
        ),
    ]
