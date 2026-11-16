import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("salao_cabeleireiro", "0011_recebimento_venda"),
    ]

    operations = [
        migrations.CreateModel(
            name="SessaoCaixa",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("operador_nome", models.CharField(blank=True, default="", max_length=160)),
                ("aberta_em", models.DateTimeField(auto_now_add=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"verbose_name": "Sessão do caixa", "ordering": ["-aberta_em"]},
        ),
        migrations.AddField(
            model_name="venda",
            name="operador_nome",
            field=models.CharField(blank=True, default="", max_length=160),
        ),
        migrations.AddField(
            model_name="venda",
            name="sessao",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="vendas",
                to="salao_cabeleireiro.sessaocaixa",
            ),
        ),
    ]
