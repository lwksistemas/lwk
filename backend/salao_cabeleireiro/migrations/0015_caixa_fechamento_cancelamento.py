import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("salao_cabeleireiro", "0014_forma_pagamento_cliente_endereco"),
    ]

    operations = [
        migrations.AddField(
            model_name="venda",
            name="cancelado_em",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="venda",
            name="cancelado_por",
            field=models.CharField(blank=True, default="", max_length=160),
        ),
        migrations.AddField(
            model_name="venda",
            name="motivo_cancelamento",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="venda",
            name="estoque_estornado",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="sessaocaixa",
            name="saldo_inicial",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=10),
        ),
        migrations.AddField(
            model_name="sessaocaixa",
            name="fechada_em",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="sessaocaixa",
            name="operador_fechamento",
            field=models.CharField(blank=True, default="", max_length=160),
        ),
        migrations.AddField(
            model_name="sessaocaixa",
            name="dinheiro_contado",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name="sessaocaixa",
            name="diferenca",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name="sessaocaixa",
            name="observacao",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.CreateModel(
            name="MovimentoCaixa",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("tipo", models.CharField(max_length=20)),
                ("valor", models.DecimalField(decimal_places=2, max_digits=10)),
                ("motivo", models.CharField(blank=True, default="", max_length=200)),
                ("operador_nome", models.CharField(blank=True, default="", max_length=160)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "sessao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="movimentos",
                        to="salao_cabeleireiro.sessaocaixa",
                    ),
                ),
            ],
            options={"verbose_name": "Movimento do caixa", "ordering": ["-created_at"]},
        ),
    ]
