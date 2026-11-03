from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0098_vinculo_produto_fornecedor"),
    ]

    operations = [
        migrations.AddField(
            model_name="produtoestoque",
            name="exige_lote",
            field=models.BooleanField(
                default=False,
                help_text="A NF-e só entra se o item tiver lote e validade. O saldo já lançado não muda.",
                verbose_name="Exigir lote e validade na entrada",
            ),
        ),
        migrations.CreateModel(
            name="CompraFornecedorEstoque",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("documento", models.CharField(blank=True, default="", max_length=20)),
                ("fornecedor_nome", models.CharField(blank=True, default="", max_length=200)),
                ("codigo", models.CharField(blank=True, default="", max_length=60)),
                ("chave", models.CharField(blank=True, default="", max_length=44)),
                ("numero_nota", models.CharField(blank=True, default="", max_length=20)),
                ("data_compra", models.DateField(blank=True, null=True)),
                ("quantidade", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("unidade", models.CharField(blank=True, default="", max_length=30)),
                ("quantidade_estoque", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("unidade_estoque", models.CharField(blank=True, default="", max_length=30)),
                ("fator", models.DecimalField(decimal_places=4, default=Decimal("1"), max_digits=10)),
                ("custo_unitario", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("lote", models.CharField(blank=True, default="", max_length=50)),
                ("validade", models.DateField(blank=True, null=True)),
                ("usuario", models.CharField(blank=True, default="", max_length=80)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("produto", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="compras_fornecedor",
                    to="clinica_beleza.produtoestoque",
                )),
            ],
            options={
                "verbose_name": "Compra de fornecedor",
                "db_table": "clinica_beleza_compra_fornecedor_estoque",
                "ordering": ["-data_compra", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="comprafornecedorestoque",
            index=models.Index(fields=["loja_id", "produto", "-created_at"], name="cb_compra_forn_prod_idx"),
        ),
        migrations.CreateModel(
            name="LoteProdutoEstoque",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("codigo", models.CharField(blank=True, default="", max_length=50, verbose_name="Lote")),
                ("validade", models.DateField(blank=True, null=True)),
                ("quantidade", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("documento", models.CharField(blank=True, default="", max_length=20)),
                ("fornecedor_nome", models.CharField(blank=True, default="", max_length=200)),
                ("numero_nota", models.CharField(blank=True, default="", max_length=20)),
                ("chave", models.CharField(blank=True, default="", max_length=44)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("produto", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="lotes_estoque",
                    to="clinica_beleza.produtoestoque",
                )),
            ],
            options={
                "verbose_name": "Lote do produto",
                "db_table": "clinica_beleza_lote_produto_estoque",
                "ordering": ["validade", "codigo"],
            },
        ),
        migrations.AddConstraint(
            model_name="loteprodutoestoque",
            constraint=models.UniqueConstraint(
                fields=("loja_id", "produto", "codigo", "validade"),
                name="cb_lote_prod_uniq",
                nulls_distinct=False,
            ),
        ),
    ]
